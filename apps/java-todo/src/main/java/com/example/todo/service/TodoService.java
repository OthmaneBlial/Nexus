package com.example.todo.service;

import com.example.todo.model.TodoItem;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class TodoService {
    private final Map<Integer, TodoItem> store = new LinkedHashMap<>();
    private int nextId = 1;

    public List<TodoItem> findAll() {
        return new ArrayList<>(store.values());
    }

    public TodoItem create(String title) {
        TodoItem item = new TodoItem(nextId, title, false, LocalDateTime.now(), LocalDateTime.now());
        store.put(item.id(), item);
        nextId++;
        return item;
    }

    public Optional<TodoItem> toggle(int id) {
        TodoItem existing = store.get(id);
        if (existing == null) {
            return Optional.empty();
        }
        TodoItem updated = existing.markCompleted(!existing.completed());
        store.put(id, updated);
        return Optional.of(updated);
    }

    public Optional<TodoItem> rename(int id, String newTitle) {
        TodoItem existing = store.get(id);
        if (existing == null) {
            return Optional.empty();
        }
        TodoItem updated = existing.rename(newTitle);
        store.put(id, updated);
        return Optional.of(updated);
    }

    public boolean delete(int id) {
        return store.remove(id) != null;
    }

    public void seedDefaults() {
        if (!store.isEmpty()) {
            return;
        }
        create("Sketch UI wireframes");
        create("Review pull requests");
        TodoItem completed = create("Ship the MVP");
        toggle(completed.id());
    }
}
