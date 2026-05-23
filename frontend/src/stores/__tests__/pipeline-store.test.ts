import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStore } from "../pipeline-store";
import type { PipelineRun } from "../../types/pipeline";

describe("usePipelineStore", () => {
  beforeEach(() => {
    usePipelineStore.getState().reset();
  });

  it("starts with empty state", () => {
    const state = usePipelineStore.getState();
    expect(state.events).toHaveLength(0);
    expect(state.isRunning).toBe(false);
    expect(state.error).toBeNull();
    expect(state.currentRun).toBeNull();
    expect(state.validations).toHaveLength(0);
    expect(state.validationSummary).toBeNull();
  });

  it("addEvent appends immutably", () => {
    const event = {
      event_type: "stage_start",
      stage: "router",
      message: "test",
      data: {},
    };
    usePipelineStore.getState().addEvent(event);
    const events = usePipelineStore.getState().events;
    expect(events).toHaveLength(1);
    expect(events[0]).toEqual(event);
  });

  it("addEvent preserves existing events", () => {
    const e1 = { event_type: "stage_start", stage: "router", message: "a", data: {} };
    const e2 = { event_type: "stage_complete", stage: "router", message: "b", data: {} };
    usePipelineStore.getState().addEvent(e1);
    usePipelineStore.getState().addEvent(e2);
    expect(usePipelineStore.getState().events).toHaveLength(2);
  });

  it("setRunning toggles isRunning", () => {
    usePipelineStore.getState().setRunning(true);
    expect(usePipelineStore.getState().isRunning).toBe(true);
    usePipelineStore.getState().setRunning(false);
    expect(usePipelineStore.getState().isRunning).toBe(false);
  });

  it("setError stores error message", () => {
    usePipelineStore.getState().setError("something failed");
    expect(usePipelineStore.getState().error).toBe("something failed");
    usePipelineStore.getState().setError(null);
    expect(usePipelineStore.getState().error).toBeNull();
  });

  it("setValidations stores items and summary", () => {
    const items = [{ category: "style", item: "test", passed: true, score: 0.9, message: "ok" }];
    const summary = { total: 1, passed: 1, failed: 0, score: 1.0, by_category: {} };
    usePipelineStore.getState().setValidations(items, summary);
    expect(usePipelineStore.getState().validations).toHaveLength(1);
    expect(usePipelineStore.getState().validationSummary).toEqual(summary);
  });

  it("reset restores initial state", () => {
    usePipelineStore.getState().addEvent({
      event_type: "stage_start",
      stage: "router",
      message: "test",
      data: {},
    });
    usePipelineStore.getState().setRunning(true);
    usePipelineStore.getState().setError("error");

    usePipelineStore.getState().reset();
    const state = usePipelineStore.getState();
    expect(state.events).toHaveLength(0);
    expect(state.isRunning).toBe(false);
    expect(state.error).toBeNull();
  });

  it("setCurrentRun stores run data", () => {
    const run: PipelineRun = {
      id: 1,
      article_id: 1,
      current_stage: "router",
      status: "running",
      started_at: "2026-01-01T00:00:00",
      completed_at: null,
    };
    usePipelineStore.getState().setCurrentRun(run);
    expect(usePipelineStore.getState().currentRun).toEqual(run);
  });

  it("setEvents replaces all events", () => {
    usePipelineStore.getState().addEvent({
      event_type: "stage_start",
      stage: "router",
      message: "a",
      data: {},
    });
    const replacement = [
      {
        event_type: "stage_start",
        stage: "outliner",
        message: "b",
        data: {},
      },
    ];
    usePipelineStore.getState().setEvents(replacement);
    expect(usePipelineStore.getState().events).toHaveLength(1);
    expect(usePipelineStore.getState().events[0].stage).toBe("outliner");
  });

  it("addEvent does not mutate previous reference", () => {
    const e1 = {
      event_type: "stage_start",
      stage: "router",
      message: "a",
      data: {},
    };
    usePipelineStore.getState().addEvent(e1);
    const firstRef = usePipelineStore.getState().events;

    usePipelineStore.getState().addEvent({
      event_type: "stage_complete",
      stage: "router",
      message: "b",
      data: {},
    });
    expect(firstRef).toHaveLength(1);
    expect(usePipelineStore.getState().events).toHaveLength(2);
  });
});
