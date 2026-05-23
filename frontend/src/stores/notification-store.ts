import { create } from "zustand";

export interface Notification {
  id: string;
  type: "gate" | "complete" | "error" | "info";
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  articleId?: number;
  runId?: number;
}

interface NotificationState {
  notifications: Notification[];
  addNotification: (n: Omit<Notification, "id" | "timestamp" | "read">) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  clearAll: () => void;
  unreadCount: () => number;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],

  addNotification: (n) =>
    set((s) => ({
      notifications: [
        {
          ...n,
          id: crypto.randomUUID(),
          timestamp: Date.now(),
          read: false,
        },
        ...s.notifications,
      ].slice(0, 50),
    })),

  markRead: (id) =>
    set((s) => ({
      notifications: s.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n,
      ),
    })),

  markAllRead: () =>
    set((s) => ({
      notifications: s.notifications.map((n) => ({ ...n, read: true })),
    })),

  clearAll: () => set({ notifications: [] }),

  unreadCount: () => get().notifications.filter((n) => !n.read).length,
}));
