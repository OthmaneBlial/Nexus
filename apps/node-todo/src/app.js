import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import express from "express";
import morgan from "morgan";
import createError from "http-errors";

import { buildRoutes } from "./routes/index.js";
import { TodoController } from "./controllers/todoController.js";
import { createDefaultStore } from "./store/memoryStore.js";

export function createApp() {
  const app = express();

  app.use(morgan("dev"));
  app.use(express.json());
  const publicDir = resolve(dirname(fileURLToPath(import.meta.url)), "../public");
  app.use(express.static(publicDir));

  const store = createDefaultStore();
  const todoController = new TodoController(store);

  app.use("/", buildRoutes(todoController));

  app.use((req, _res, next) => {
    next(createError(404, `Not found: ${req.originalUrl}`));
  });

  // eslint-disable-next-line no-unused-vars
  app.use((err, _req, res, _next) => {
    const status = err.status || 500;
    res.status(status).json({
      error: {
        status,
        message: err.message || "Internal Server Error",
      },
    });
  });

  return app;
}
