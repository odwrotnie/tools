"""
Prosty skrypt do sprawdzania numeru telefonu z użyciem biblioteki `ignorant`.

Wymagania:
- python -m pip install ignorant httpx trio

Przykład:
  python3 phone.py --country 33 --phone 644637111
  python3 phone.py --country 48 --phone 501234567 --modules shopping.amazon,social_media.instagram

Biblioteka: https://github.com/megadose/ignorant
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass
import pkgutil
from typing import Callable, List, Optional, Sequence, Tuple

import trio
import httpx


# Domyślna lista modułów do uruchomienia. Każda pozycja to (moduł, funkcja).
# Zgodnie z README biblioteki, np. amazon: ignorant.modules.shopping.amazon:amazon
DEFAULT_MODULES: Sequence[Tuple[str, str]] = (
    ("shopping.amazon", "amazon"),
    ("social_media.instagram", "instagram"),
    ("social_media.snapchat", "snapchat"),
)


@dataclass
class LoadedModule:
    module_path: str
    function_name: str
    function: Callable[..., object]


def _discover_all_ignorant_module_specs() -> List[Tuple[str, str]]:
    """Zwraca listę wszystkich możliwych modułów ignorant w formacie (rel_path, func_name).

    Przechodzimy rekursywnie po przestrzeni `ignorant.modules.*` i dla każdego modułu
    bierzemy nazwę funkcji równą ostatniemu segmentowi ścieżki.
    Rzeczywiste istnienie funkcji zweryfikuje później `load_ignorant_functions`.
    """
    try:
        root_pkg = importlib.import_module("ignorant")
    except Exception:
        return []

    search_path = getattr(root_pkg, "__path__", None)
    if not search_path:
        return []

    discovered: List[Tuple[str, str]] = []
    prefix = "ignorant.modules."
    for modinfo in pkgutil.walk_packages(search_path, prefix=root_pkg.__name__ + "."):
        full_name = modinfo.name
        if modinfo.ispkg:
            continue
        if not full_name.startswith(prefix):
            continue
        rel_name = full_name[len(prefix) :]
        func_name = rel_name.split(".")[-1]
        if func_name:
            discovered.append((rel_name, func_name))
    return discovered


def parse_modules_arg(arg_value: Optional[str]) -> Sequence[Tuple[str, str]]:
    """Parsuje wartość argumentu --modules.

    Obsługiwane formaty wejścia (rozdzielane przecinkami):
    - "shopping.amazon"  → funkcja przyjmowana jako ostatni segment, np. "amazon"
    - "shopping.amazon:amazon" → jawnie moduł i funkcja
    """
    if not arg_value:
        # Domyślnie: skanuj wszystkie dostępne moduły ignorant
        discovered = _discover_all_ignorant_module_specs()
        return discovered if discovered else DEFAULT_MODULES

    # Specjalna wartość pozwalająca uruchomić WSZYSTKIE dostępne moduły
    normalized = arg_value.strip().lower().strip("'\"")
    if normalized in {"all", "*"}:
        discovered = _discover_all_ignorant_module_specs()
        return discovered if discovered else DEFAULT_MODULES

    result: List[Tuple[str, str]] = []
    for item in arg_value.split(","):
        item = item.strip().strip("'\"")
        if not item:
            continue
        if ":" in item:
            module_path, func_name = item.split(":", 1)
            module_path = module_path.strip().strip("'\"")
            func_name = func_name.strip().strip("'\"")
            if not module_path or not func_name:
                raise ValueError(f"Nieprawidłowa specyfikacja modułu: '{item}'")
            result.append((module_path, func_name))
        else:
            # Przyjmujemy, że nazwa funkcji = ostatni segment modułu
            last_segment = item.split(".")[-1]
            if not last_segment:
                raise ValueError(f"Nieprawidłowa specyfikacja modułu: '{item}'")
            result.append((item, last_segment))
    return result


def load_ignorant_functions(module_specs: Sequence[Tuple[str, str]]) -> List[LoadedModule]:
    """Ładuje funkcje modułów ignorant.

    Oczekuje nazw w przestrzeni "ignorant.modules.<ścieżka>" oraz nazw funkcji.
    Pomija pozycje, których nie da się zaimportować, wypisując ostrzeżenie na stderr.
    """
    loaded: List[LoadedModule] = []
    for rel_module_path, func_name in module_specs:
        # Ignoruj aliasy typu 'all'/'*' jeśli gdzieś przeniknęły
        if rel_module_path in {"all", "*"}:
            continue
        full_module = f"ignorant.modules.{rel_module_path}"
        try:
            mod = importlib.import_module(full_module)
        except Exception:
            # Ciche pominięcie modułów, których nie da się zaimportować w środowisku
            continue

        try:
            func = getattr(mod, func_name)
        except AttributeError:
            # Brak oczekiwanej funkcji – pomijamy bez ostrzegania
            continue

        loaded.append(LoadedModule(module_path=full_module, function_name=func_name, function=func))

    if not loaded:
        raise RuntimeError(
            "Nie udało się załadować żadnego modułu ignorant. Sprawdź instalację pakietu 'ignorant'"
        )

    return loaded


async def run_checks(country_code: str, phone: str, modules_to_run: Sequence[LoadedModule]) -> List[dict]:
    """Uruchamia równolegle wskazane moduły ignorant dla podanego numeru."""
    out: List[dict] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        async with trio.open_nursery() as nursery:
            for loaded_module in modules_to_run:
                nursery.start_soon(
                    _invoke_module,
                    loaded_module,
                    phone,
                    country_code,
                    client,
                    out,
                )

    return out


async def _invoke_module(
    loaded_module: LoadedModule,
    phone: str,
    country_code: str,
    client: httpx.AsyncClient,
    out: List[dict],
) -> None:
    """Wywołuje pojedynczy moduł ignorant i łapie wyjątki, by nie przerywać całości."""
    try:
        # API biblioteki (zgodnie z README):
        # await <module_func>(phone, country_code, client, out)
        await loaded_module.function(phone, country_code, client, out)
    except Exception as exc:  # pragma: no cover - defensywne zabezpieczenie
        out.append(
            {
                "name": loaded_module.function_name,
                "domain": loaded_module.module_path,
                "method": "unknown",
                "frequent_rate_limit": "Unknown",
                "rateLimit": "Unknown",
                "exists": "Unknown",
                "error": str(exc),
            }
        )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sprawdzanie numeru telefonu na serwisach wspieranych przez ignorant (asynchronicznie)",
    )
    parser.add_argument("--country", required=True, help="Kod kraju, np. 33, 48")
    parser.add_argument("--phone", required=True, help="Numer telefonu bez prefiksu kraju")
    parser.add_argument(
        "--modules",
        help=(
            "Lista modułów oddzielona przecinkami. Każdy jako 'sciezka.do.modulu' lub 'sciezka.do.modulu:nazwa_funkcji'.\n"
            "Możesz też podać 'all' lub '*' aby przeszukać wszystkie dostępne moduły ignorant.\n"
            "Domyślnie: shopping.amazon, social_media.instagram, social_media.snapchat"
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Ładniejszy (wcięty) JSON na wyjściu",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        module_specs = parse_modules_arg(args.modules)
        loaded = load_ignorant_functions(module_specs)
    except Exception as exc:
        print(f"Błąd inicjalizacji modułów: {exc}", file=sys.stderr)
        return 2

    try:
        results = trio.run(run_checks, args.country, args.phone, loaded)
    except Exception as exc:  # pragma: no cover - defensywne
        print(f"Błąd wykonania: {exc}", file=sys.stderr)
        return 3

    if args.pretty:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


def check_phone_sync(country_code: str, phone: str, modules_str: Optional[str] = None) -> List[dict]:
    """Wygodny wrapper do użycia synchronicznie (np. w GUI)."""
    module_specs = parse_modules_arg(modules_str)
    loaded = load_ignorant_functions(module_specs)
    return trio.run(run_checks, country_code, phone, loaded)


