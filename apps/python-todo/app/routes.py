from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .dependencies import get_store
from .schemas import TodoCreate, TodoResponse, TodoUpdate
from .storage import TodoStore

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("/", response_model=list[TodoResponse])
def list_todos(store: TodoStore = Depends(get_store)) -> list[TodoResponse]:
    return store.list_items()


@router.post("/", response_model=TodoResponse, status_code=201)
def create_todo(payload: TodoCreate, store: TodoStore = Depends(get_store)) -> TodoResponse:
    return store.add_item(payload)


@router.patch("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, payload: TodoUpdate, store: TodoStore = Depends(get_store)) -> TodoResponse:
    try:
        return store.update_item(todo_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Todo not found") from exc


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, store: TodoStore = Depends(get_store)) -> None:
    try:
        store.delete_item(todo_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Todo not found") from exc
