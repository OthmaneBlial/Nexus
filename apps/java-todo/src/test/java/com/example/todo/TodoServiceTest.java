package com.example.todo;

import com.example.todo.model.TodoItem;
import com.example.todo.service.TodoService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class TodoServiceTest {
    private TodoService service;

    @BeforeEach
    void setUp() {
        service = new TodoService();
    }

    @Test
    void createAddsTask() {
        TodoItem item = service.create("Write tests");

        List<TodoItem> items = service.findAll();
        assertThat(items).contains(item);
    }

    @Test
    void toggleChangesCompletionState() {
        TodoItem item = service.create("Toggle me");

        service.toggle(item.id());
        assertThat(service.findAll()).anyMatch(TodoItem::completed);
    }
}
