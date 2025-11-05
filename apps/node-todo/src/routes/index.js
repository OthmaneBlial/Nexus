import { Router } from "express";
import { createTodoRouter } from "./todos.js";

export function buildRoutes(todoController) {
  const router = Router();

  router.get("/", (_req, res) => {
    res.json({ message: "Node TODO API", docs: "/docs" });
  });

  router.use("/todos", createTodoRouter(todoController));

  return router;
}
