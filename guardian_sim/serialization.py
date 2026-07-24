"""JSON serialization helpers for simulator-produced numeric values."""

from __future__ import annotations


def json_default(value: object) -> object:
    """Convert NumPy-style scalars and arrays into JSON-native values."""

    item = getattr(value, "item", None)
    if callable(item):
        return item()

    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        return tolist()

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
