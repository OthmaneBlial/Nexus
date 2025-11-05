package com.example.todo.console;

import com.example.todo.model.TodoItem;
import com.example.todo.service.TodoService;

import java.time.format.DateTimeFormatter;
import java.util.Scanner;

public class TodoConsole {
    private final TodoService service;
    private final Scanner scanner = new Scanner(System.in);

    public TodoConsole(TodoService service) {
        this.service = service;
    }

    public void run() {
        service.seedDefaults();
        BannerPrinter.printBanner();
        println("\n=== Java TODO Demo ===\n");
        boolean running = true;
        while (running) {
            render();
            println("\nCommands: [a]dd  [t]oggle  [r]ename  [d]elete  [q]uit");
            String input = prompt("> ").trim().toLowerCase();
            switch (input) {
                case "a" -> handleAdd();
                case "t" -> handleToggle();
                case "r" -> handleRename();
                case "d" -> handleDelete();
                case "q" -> running = false;
                default -> println("Unknown command: " + input);
            }
        }
        println("\nGoodbye!");
    }

    private void render() {
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        println("\nCurrent tasks:");
        for (TodoItem item : service.findAll()) {
            String status = item.completed() ? "✔" : " ";
            println(String.format("[%s] #%d %-20s (updated %s)", status, item.id(), item.title(), item.updatedAt().format(fmt)));
        }
    }

    private void handleAdd() {
        String title = prompt("Title: ");
        if (!title.isBlank()) {
            service.create(title);
        }
    }

    private void handleToggle() {
        int id = promptNumber("Toggle task id: ");
        service.toggle(id).orElseGet(() -> {
            println("Task not found.");
            return null;
        });
    }

    private void handleRename() {
        int id = promptNumber("Rename task id: ");
        String title = prompt("New title: ");
        service.rename(id, title).orElseGet(() -> {
            println("Task not found.");
            return null;
        });
    }

    private void handleDelete() {
        int id = promptNumber("Delete task id: ");
        if (!service.delete(id)) {
            println("Task not found.");
        }
    }

    private void println(String text) {
        System.out.println(text);
    }

    private String prompt(String text) {
        System.out.print(text);
        return scanner.nextLine();
    }

    private int promptNumber(String text) {
        try {
            return Integer.parseInt(prompt(text).trim());
        } catch (NumberFormatException ex) {
            println("Not a number.");
            return -1;
        }
    }
}
