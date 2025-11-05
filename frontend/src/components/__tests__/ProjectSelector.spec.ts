import { describe, it, expect } from "vitest";
import { render, fireEvent } from "@testing-library/vue";
import ProjectSelector from "../ProjectSelector.vue";

describe("ProjectSelector", () => {
  it("emits select when a directory is clicked", async () => {
    const entries = [
      { name: "backend", path: "backend", type: "directory" },
      { name: "README.md", path: "README.md", type: "file" },
    ];

    const { getByText, emitted } = render(ProjectSelector, {
      props: {
        currentPath: ".",
        entries,
        loading: false,
        error: null,
      },
    });

    await fireEvent.click(getByText("backend"));

    const selectEvents = emitted().select as unknown[] | undefined;
    expect(selectEvents).toBeTruthy();
    const firstPayload = Array.isArray(selectEvents) ? (selectEvents[0] as unknown[])?.[0] : undefined;
    expect(firstPayload).toEqual(entries[0]);
  });
});
