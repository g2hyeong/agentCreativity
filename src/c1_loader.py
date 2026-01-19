# src/c1_loader.py
import json
import os
from typing import Dict, Tuple

_CACHE: Dict[Tuple[str, str], dict] = {}

def _root_dir() -> str:
    # src/ -> EscapeBench/
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _path(kind: str, game_id: str) -> str:
    # kind: "tool" or "item"
    return os.path.join(_root_dir(), "data", "c1", kind, f"{game_id}.json")

def load_c1(kind: str, game_id: str) -> dict:
    """
    kind: "tool" | "item"
    game_id: e.g., "game3-2"
    """
    key = (kind, game_id)
    if key in _CACHE:
        return _CACHE[key]

    p = _path(kind, game_id)
    if not os.path.exists(p):
        _CACHE[key] = {}
        return {}

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    _CACHE[key] = data
    return data
