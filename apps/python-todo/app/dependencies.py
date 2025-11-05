from __future__ import annotations

from typing import Optional

from .storage import TodoStore

_store: Optional[TodoStore] = None


def get_store() -> TodoStore:
    global _store
    if _store is None:
        _store = TodoStore()
    return _store
