package com.example.todo;

import com.example.todo.config.TodoConfig;
import com.example.todo.console.TodoConsole;

public final class TodoApplication {
    private TodoApplication() {
    }

    public static void main(String[] args) {
        TodoConfig config = new TodoConfig();
        TodoConsole console = config.todoConsole();
        console.run();
    }
}
