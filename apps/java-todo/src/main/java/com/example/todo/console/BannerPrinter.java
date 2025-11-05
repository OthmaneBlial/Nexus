package com.example.todo.console;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

public final class BannerPrinter {
    private BannerPrinter() {
    }

    public static void printBanner() {
        try (InputStream in = BannerPrinter.class.getResourceAsStream("/banner.txt")) {
            if (in == null) {
                return;
            }
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
                reader.lines().forEach(System.out::println);
            }
        } catch (IOException ignored) {
            // best effort banner display
        }
    }
}
