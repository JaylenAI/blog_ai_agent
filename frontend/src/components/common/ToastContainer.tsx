import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { Icons } from "./Icons";

const AUTO_DISMISS_MS = 5000;

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts);
  const removeToast = useAppStore((s) => s.removeToast);

  useEffect(() => {
    if (toasts.length === 0) return;

    const latest = toasts[toasts.length - 1] as typeof toasts[number] | undefined;
    if (!latest) return;
    const timer = setTimeout(() => removeToast(latest.id), AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [toasts, removeToast]);

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: 20,
        right: 20,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        maxWidth: 400,
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: 10,
            padding: "12px 16px",
            borderRadius: "var(--radius)",
            fontSize: 13,
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
