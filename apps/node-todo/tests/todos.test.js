import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app.js";

describe("TODO API", () => {
  const app = createApp();

  it("lists seeded todos", async () => {
    const response = await request(app).get("/todos");
    expect(response.status).toBe(200);
    expect(response.body.length).toBeGreaterThan(0);
  });

  it("creates, updates, and deletes a todo", async () => {
    const created = await request(app).post("/todos").send({ title: "Write API docs" });
    expect(created.status).toBe(201);

    const updated = await request(app).patch(`/todos/${created.body.id}`).send({ completed: true });
    expect(updated.status).toBe(200);
    expect(updated.body.completed).toBe(true);

    const deleted = await request(app).delete(`/todos/${created.body.id}`);
    expect(deleted.status).toBe(204);
  });
});
