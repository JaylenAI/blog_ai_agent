import { describe, it, expect, beforeEach, vi } from "vitest";
import { useToastStore } from "../toast-store";
import { act } from "@testing-library/react";

vi.stubGlobal("crypto", {
  randomUUID: () => `toast-${Math.random().toString(36).slice(2, 8)}`,
});

beforeEach(() => {
  act(() => useToastStore.setState({ toasts: [] }));
});

describe("useToastStore", () => {
  it("starts with empty toasts", () => {
    expect(useToastStore.getState().toasts).toEqual([]);
  });

  it("addToast appends a toast with generated id", () => {
    act(() =>
      useToastStore.getState().addToast({
        type: "success",
        message: "완료!",
      }),
    );
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].type).toBe("success");
    expect(toasts[0].message).toBe("완료!");
    expect(toasts[0].id).toBeTruthy();
  });

  it("addToast appends multiple toasts in order", () => {
    act(() => {
      useToastStore.getState().addToast({ type: "error", message: "에러 1" });
      useToastStore.getState().addToast({ type: "info", message: "정보 1" });
      useToastStore.getState().addToast({ type: "success", message: "성공 1" });
    });
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(3);
    expect(toasts[0].type).toBe("error");
    expect(toasts[1].type).toBe("info");
    expect(toasts[2].type).toBe("success");
  });

  it("removeToast removes by id", () => {
    act(() => {
      useToastStore.getState().addToast({ type: "error", message: "삭제 대상" });
      useToastStore.getState().addToast({ type: "info", message: "유지" });
    });
    const targetId = useToastStore.getState().toasts[0].id;
    act(() => useToastStore.getState().removeToast(targetId));
    const remaining = useToastStore.getState().toasts;
    expect(remaining).toHaveLength(1);
    expect(remaining[0].message).toBe("유지");
  });

  it("removeToast with unknown id does nothing", () => {
    act(() =>
      useToastStore.getState().addToast({ type: "info", message: "test" }),
    );
    act(() => useToastStore.getState().removeToast("nonexistent"));
    expect(useToastStore.getState().toasts).toHaveLength(1);
  });

  it("each toast gets unique id", () => {
    act(() => {
      useToastStore.getState().addToast({ type: "info", message: "a" });
      useToastStore.getState().addToast({ type: "info", message: "b" });
    });
    const [a, b] = useToastStore.getState().toasts;
    expect(a.id).not.toBe(b.id);
  });
});
