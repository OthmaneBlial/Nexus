# Java TODO Demo

Maven-based Java 17 console app that exercises simple service logic and tests.

## Build & run

```bash
mvn verify
mvn exec:java -Dexec.mainClass="com.example.todo.TodoApplication"
```

The console menu lets you add, toggle, rename, and delete tasks. Seed data appears on startup.
