import { randomUUID } from "node:crypto";

export class MemoryStore {
  constructor(seed = []) {
    this.items = [...seed];
  }

  list() {
    return this.items;
  }

  create({ title, description = "" }) {
    const item = {
      id: randomUUID().slice(0, 8),
      title,
      description,
      completed: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.items.push(item);
    return item;
  }

  update(id, data) {
    const index = this.items.findIndex((item) => item.id === id);
    if (index === -1) {
      return null;
    }
    const updated = {
      ...this.items[index],
      ...data,
      updatedAt: new Date().toISOString(),
    };
    this.items[index] = updated;
    return updated;
  }

  remove(id) {
    const index = this.items.findIndex((item) => item.id === id);
    if (index === -1) {
      return false;
    }
    this.items.splice(index, 1);
    return true;
  }
}

export function createDefaultStore() {
  return new MemoryStore([
    {
      id: "plan-ui",
      title: "Plan backlog",
      description: "Define the work for this sprint",
      completed: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: "demo-api",
      title: "Implement CRUD demo",
      description: "Provide endpoints for the dashboard sample",
      completed: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ]);
}
