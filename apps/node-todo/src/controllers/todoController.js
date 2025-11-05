import createHttpError from "http-errors";

export class TodoController {
  constructor(store) {
    this.store = store;
  }

  list = (_req, res) => {
    res.json(this.store.list());
  };

  create = (req, res, next) => {
    const { title, description } = req.body ?? {};
    if (typeof title !== "string" || title.trim().length === 0) {
      return next(createHttpError(400, "Title is required"));
    }
    const todo = this.store.create({ title: title.trim(), description });
    res.status(201).json(todo);
  };

  update = (req, res, next) => {
    const { id } = req.params;
    const updates = {};
    if (typeof req.body?.title === "string") {
      updates.title = req.body.title.trim();
    }
    if (typeof req.body?.description === "string") {
      updates.description = req.body.description.trim();
    }
    if (typeof req.body?.completed === "boolean") {
      updates.completed = req.body.completed;
    }

    const todo = this.store.update(id, updates);
    if (!todo) {
      return next(createHttpError(404, "Todo not found"));
    }
    res.json(todo);
  };

  remove = (req, res, next) => {
    const { id } = req.params;
    const removed = this.store.remove(id);
    if (!removed) {
      return next(createHttpError(404, "Todo not found"));
    }
    res.status(204).end();
  };
}
