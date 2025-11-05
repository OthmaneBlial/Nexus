package com.example.todo.model;

import java.time.LocalDateTime;

public record TodoItem(int id, String title, boolean completed, LocalDateTime createdAt, LocalDateTime updatedAt) {
    public TodoItem markCompleted(boolean state) {
        return new TodoItem(id, title, state, createdAt, LocalDateTime.now());
    }

    public TodoItem rename(String newTitle) {
        return new TodoItem(id, newTitle, completed, createdAt, LocalDateTime.now());
    }
}
