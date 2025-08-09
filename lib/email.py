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


DEFAULT_MODULES: Sequence[Tuple[str, str]] = (
    ("social_media.instagram", "instagram"),
    ("social_media.snapchat", "snapchat"),
    ("shopping.amazon", "amazon"),
)


@dataclass
class LoadedModule:
    module_path: str
    function_name: str
    function: Callable[..., object]


def _discover_all_holehe_module_specs() -> List[Tuple[str, str]]:
    try:
        root_pkg = importlib.import_module("holehe")
    except Exception:
        return []

    search_path = getattr(root_pkg, "__path__", None)
    if not search_path:
        return []

    discovered: List[Tuple[str, str]] = []
    prefix = "holehe.modules."
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
    if not arg_value:
        discovered = _discover_all_holehe_module_specs()
        return discovered if discovered else DEFAULT_MODULES

    normalized = arg_value.strip().lower().strip("'\"")
    if normalized in {"all", "*"}:
        discovered = _discover_all_holehe_module_specs()
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
            last_segment = item.split(".")[-1]
            if not last_segment:
                raise ValueError(f"Nieprawidłowa specyfikacja modułu: '{item}'")
            result.append((item, last_segment))
    return result


def load_holehe_functions(module_specs: Sequence[Tuple[str, str]]) -> List[LoadedModule]:
    loaded: List[LoadedModule] = []
    for rel_module_path, func_name in module_specs:
        if rel_module_path in {"all", "*"}:
            continue
        full_module = f"holehe.modules.{rel_module_path}"
        try:
            mod = importlib.import_module(full_module)
        except Exception:
            continue

        try:
            func = getattr(mod, func_name)
        except AttributeError:
            continue

        loaded.append(LoadedModule(module_path=full_module, function_name=func_name, function=func))

    if not loaded:
        raise RuntimeError(
            "Nie udało się załadować żadnego modułu holehe. Sprawdź instalację pakietu 'holehe'"
        )

    return loaded


async def run_checks(email: str, modules_to_run: Sequence[LoadedModule]) -> List[dict]:
    out: List[dict] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        async with trio.open_nursery() as nursery:
            for loaded_module in modules_to_run:
                nursery.start_soon(
                    _invoke_module,
                    loaded_module,
                    email,
                    client,
                    out,
                )

    return out


async def _invoke_module(
    loaded_module: LoadedModule,
    email: str,
    client: httpx.AsyncClient,
    out: List[dict],
) -> None:
    try:
        await loaded_module.function(email, client, out)
    except Exception as exc:  # pragma: no cover
        out.append(
            {
                "name": loaded_module.function_name,
                "domain": loaded_module.module_path,
                "rateLimit": "Unknown",
                "exists": "Unknown",
                "error": str(exc),
            }
        )


def check_email_sync(email: str, modules_str: Optional[str] = None) -> List[dict]:
    module_specs = parse_modules_arg(modules_str)
    loaded = load_holehe_functions(module_specs)
    return trio.run(run_checks, email, loaded)


