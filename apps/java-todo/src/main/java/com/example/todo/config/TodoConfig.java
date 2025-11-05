package com.example.todo.config;

import com.example.todo.console.TodoConsole;
import com.example.todo.service.TodoService;

public class TodoConfig {
    public TodoService todoService() {
        TodoService service = new TodoService();
        service.seedDefaults();
        return service;
    }

    public TodoConsole todoConsole() {
        return new TodoConsole(todoService());
    }
}
