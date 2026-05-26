import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { TOAST } from "../../constants/ui";
import { Icons } from "./Icons";

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);
  const removeToast = useAppStore((s) => s.removeToast);

  useEffect(() => {
    if (toasts.length === 0) return;

    const timers = toasts.map((toast) =>
      setTimeout(() => removeToast(toast.id), TOAST.AUTO_DISMISS_MS),
    );
    return () => timers.forEach(clearTimeout);
  }, [toasts, removeToast]);

  if (toasts.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="알림"
      aria-live="polite"
      style={{
        position: "fixed",
        bottom: TOAST.POSITION_BOTTOM,
        right: TOAST.POSITION_RIGHT,
        zIndex: TOAST.Z_INDEX,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        maxWidth: TOAST.MAX_WIDTH,
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="alert"
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: TOAST.GAP,
            padding: "12px 16px",
            borderRadius: "var(--radius)",
            fontSize: TOAST.FONT_SIZE,
            lineHeight: 1.5,
            color: "var(--text)",
            background:
              toast.type === "error"
                ? "var(--danger-bg, oklch(40% 0.15 25 / 0.15))"
                : toast.type === "success"
                  ? "var(--success-bg, oklch(55% 0.15 145 / 0.15))"
                  : "var(--bg-elev)",
            border: `1px solid ${
              toast.type === "error"
                ? "var(--danger, oklch(60% 0.2 25))"
                : toast.type === "success"
                  ? "var(--success)"
                  : "var(--border)"
            }`,
            boxShadow: "0 4px 16px oklch(0% 0 0 / 0.2)",
            animation: "rise 0.2s ease",
          }}
        >
          <span
            style={{
              flexShrink: 0,
              marginTop: 1,
              color:
                toast.type === "error"
                  ? "var(--danger, oklch(60% 0.2 25))"
                  : toast.type === "success"
                    ? "var(--success)"
                    : "var(--accent)",
            }}
          >
            {toast.type === "error" ? (
              <Icons.X s={14} w={2} />
            ) : (
              <Icons.Check s={14} w={2} />
            )}
          </span>
          <span style={{ flex: 1, minWidth: 0 }}>{toast.message}</span>
          <button
            onClick={() => removeToast(toast.id)}
            style={{
              flexShrink: 0,
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "var(--text-muted)",
              padding: 0,
              lineHeight: 1,
            }}
          >
            <Icons.X s={12} w={1.5} />
          </button>
        </div>
      ))}
    </div>
  );
}
