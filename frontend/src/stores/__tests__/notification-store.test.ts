import { describe, it, expect, beforeEach, vi } from "vitest";
import { useNotificationStore } from "../notification-store";
import { act } from "@testing-library/react";

vi.stubGlobal("crypto", {
  randomUUID: () => `uuid-${Math.random().toString(36).slice(2, 8)}`,
});

beforeEach(() => {
  act(() => useNotificationStore.setState({ notifications: [] }));
});

describe("useNotificationStore", () => {
  it("starts with empty notifications", () => {
    expect(useNotificationStore.getState().notifications).toEqual([]);
  });

  it("addNotification adds to front with generated id and timestamp", () => {
    act(() =>
      useNotificationStore.getState().addNotification({
        type: "gate",
        title: "Gate 1",
        message: "검수 대기",
      }),
    );
    const notifs = useNotificationStore.getState().notifications;
    expect(notifs).toHaveLength(1);
    expect(notifs[0].type).toBe("gate");
    expect(notifs[0].title).toBe("Gate 1");
    expect(notifs[0].read).toBe(false);
    expect(notifs[0].id).toBeTruthy();
    expect(notifs[0].timestamp).toBeGreaterThan(0);
  });

  it("addNotification prepends (newest first)", () => {
    act(() => {
      useNotificationStore.getState().addNotification({
        type: "info",
        title: "First",
        message: "msg1",
      });
      useNotificationStore.getState().addNotification({
        type: "complete",
        title: "Second",
        message: "msg2",
      });
    });
    const notifs = useNotificationStore.getState().notifications;
    expect(notifs[0].title).toBe("Second");
    expect(notifs[1].title).toBe("First");
  });

  it("caps at 50 notifications", () => {
    act(() => {
      for (let i = 0; i < 55; i++) {
        useNotificationStore.getState().addNotification({
          type: "info",
          title: `N${i}`,
          message: `msg${i}`,
        });
      }
    });
    expect(useNotificationStore.getState().notifications).toHaveLength(50);
  });

  it("markRead marks a single notification", () => {
    act(() =>
      useNotificationStore.getState().addNotification({
        type: "error",
        title: "Err",
        message: "오류",
      }),
    );
    const id = useNotificationStore.getState().notifications[0].id;
    act(() => useNotificationStore.getState().markRead(id));
    expect(useNotificationStore.getState().notifications[0].read).toBe(true);
  });

  it("markRead does not affect other notifications", () => {
    act(() => {
      useNotificationStore.getState().addNotification({
        type: "info",
        title: "A",
        message: "a",
      });
      useNotificationStore.getState().addNotification({
        type: "info",
        title: "B",
        message: "b",
      });
    });
    const first = useNotificationStore.getState().notifications[1];
    act(() => useNotificationStore.getState().markRead(first.id));
    expect(useNotificationStore.getState().notifications[0].read).toBe(false);
    expect(useNotificationStore.getState().notifications[1].read).toBe(true);
  });

  it("markAllRead marks everything", () => {
    act(() => {
      useNotificationStore.getState().addNotification({
        type: "gate",
        title: "G",
        message: "g",
      });
      useNotificationStore.getState().addNotification({
        type: "complete",
        title: "C",
        message: "c",
      });
    });
    act(() => useNotificationStore.getState().markAllRead());
    const allRead = useNotificationStore
      .getState()
      .notifications.every((n) => n.read);
    expect(allRead).toBe(true);
  });

  it("clearAll removes all notifications", () => {
    act(() =>
      useNotificationStore.getState().addNotification({
        type: "info",
        title: "T",
        message: "m",
      }),
    );
    act(() => useNotificationStore.getState().clearAll());
    expect(useNotificationStore.getState().notifications).toEqual([]);
  });

  it("unreadCount returns correct number", () => {
    act(() => {
      useNotificationStore.getState().addNotification({
        type: "info",
        title: "A",
        message: "a",
      });
      useNotificationStore.getState().addNotification({
        type: "error",
        title: "B",
        message: "b",
      });
    });
    expect(useNotificationStore.getState().unreadCount()).toBe(2);
    const id = useNotificationStore.getState().notifications[0].id;
    act(() => useNotificationStore.getState().markRead(id));
    expect(useNotificationStore.getState().unreadCount()).toBe(1);
  });

  it("preserves optional fields (articleId, runId)", () => {
    act(() =>
      useNotificationStore.getState().addNotification({
        type: "gate",
        title: "Gate",
        message: "msg",
        articleId: 5,
        runId: 10,
      }),
    );
    const n = useNotificationStore.getState().notifications[0];
    expect(n.articleId).toBe(5);
    expect(n.runId).toBe(10);
  });
});
