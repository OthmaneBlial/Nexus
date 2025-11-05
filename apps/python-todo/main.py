from __future__ import annotations

from fastapi import FastAPI

from app.routes import router


def create_app() -> FastAPI:
    application = FastAPI(title="Python TODO API", version="0.2.0")
    application.include_router(router)
    return application


app = create_app()


@app.on_event("startup")
def seed_data() -> None:
    from app.dependencies import get_store
    from app.schemas import TodoCreate

    store = get_store()
    if store.is_empty():
        store.add_item(TodoCreate(title="Review documentation", description="Read the project README"))
        store.add_item(TodoCreate(title="Implement a new feature"))
        store.add_item(TodoCreate(title="Write tests", description="Cover API endpoints with pytest + httpx"))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
