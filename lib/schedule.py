from __future__ import annotations

from typing import Dict, List, Tuple


def optimize_schedule(
    preferences: Dict[str, Dict[str, int]]
) -> Tuple[Dict[str, str], int]:
    """
    Optimize duty schedule using OR-Tools CP-SAT.

    Input structure:
      preferences[person][day] = score in [0..10]

    Hard constraints:
      - exactly one person per day
      - if score == 0, that person cannot work that day

    Objective:
      - maximize total sum of assigned scores

    Returns:
      (assignments, total_score)
        assignments: dict of {day: person}
        total_score: int objective value
    """

    try:
        import importlib
        cp_model_mod = importlib.import_module("ortools.sat.python.cp_model")
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Pakiet 'ortools' nie jest dostępny. Zainstaluj go (np. pip install ortools)."
        ) from exc

    if not preferences:
        return {}, 0

    persons: List[str] = sorted(preferences.keys())

    # Collect all days across persons (defensive)
    days_set = set()
    for days_map in preferences.values():
        days_set.update(days_map.keys())
    days: List[str] = sorted(days_set)

    model = cp_model_mod.CpModel()

    # Decision variables: x[p, d] in {0,1}
    x: Dict[Tuple[str, str], object] = {}
    for p in persons:
        for d in days:
            score = int(preferences.get(p, {}).get(d, 0))
            if score == 0:
                # Forbidden assignment - keep a fixed 0 var to simplify constraints
                x[(p, d)] = model.NewConstant(0)
            else:
                x[(p, d)] = model.NewBoolVar(f"x_{p}_{d}")

    # Exactly one person per day
    for d in days:
        model.Add(sum(x[(p, d)] for p in persons) == 1)

    # Objective: maximize total preference
    model.Maximize(
        sum(int(preferences[p].get(d, 0)) * x[(p, d)] for p in persons for d in days)
    )

    solver = cp_model_mod.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status not in (cp_model_mod.OPTIMAL, cp_model_mod.FEASIBLE):
        raise RuntimeError("Nie znaleziono rozwiązania harmonogramu.")

    assignments: Dict[str, str] = {}
    total_score = 0
    for d in days:
        chosen_person = None
        chosen_score = 0
        for p in persons:
            var = x[(p, d)]
            if solver.Value(var) == 1:
                chosen_person = p
                chosen_score = int(preferences[p].get(d, 0))
                break
        if chosen_person is None:
            # Shouldn't happen due to ==1 constraint, but guard anyway
            raise RuntimeError(f"Dzień {d}: brak przypisanej osoby w rozwiązaniu.")
        assignments[d] = chosen_person
        total_score += chosen_score

    return assignments, total_score


