from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .schemas import TodoCreate, TodoResponse, TodoUpdate


@dataclass
class TodoItem:
    title: str
    completed: bool = False
    description: Optional[str] = None


class TodoStore:
    """Simple in-memory store for demonstration purposes."""

    def __init__(self) -> None:
        self._items: Dict[int, TodoItem] = {}
        self._next_id = 1

    def is_empty(self) -> bool:
        return not self._items

    def list_items(self) -> List[TodoResponse]:
        return [
            TodoResponse(id=item_id, title=item.title, description=item.description, completed=item.completed)
            for item_id, item in sorted(self._items.items())
        ]

    def add_item(self, payload: TodoCreate) -> TodoResponse:
        item = TodoItem(title=payload.title, description=payload.description)
        item_id = self._next_id
        self._items[item_id] = item
        self._next_id += 1
        return TodoResponse(id=item_id, title=item.title, description=item.description, completed=item.completed)

    def update_item(self, item_id: int, payload: TodoUpdate) -> TodoResponse:
        if item_id not in self._items:
            raise KeyError(item_id)

        original = self._items[item_id]
        updated = TodoItem(
            title=payload.title or original.title,
            description=payload.description if payload.description is not None else original.description,
            completed=payload.completed if payload.completed is not None else original.completed,
        )
        self._items[item_id] = updated
        return TodoResponse(id=item_id, title=updated.title, description=updated.description, completed=updated.completed)

    def delete_item(self, item_id: int) -> None:
        if item_id in self._items:
            del self._items[item_id]
        else:
            raise KeyError(item_id)
