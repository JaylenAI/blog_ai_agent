import { useEffect } from "react";
import { Icons } from "./Icons";

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "default";
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmModal({
  title,
  message,
  confirmLabel = "확인",
  cancelLabel = "취소",
  variant = "default",
  onConfirm,
  onCancel,
}: Props) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onCancel]);

  return (
    <div className="confirm-overlay" onClick={onCancel}>
      <div
        className="confirm-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="confirm-header">
          <span className="confirm-title" id="confirm-modal-title">{title}</span>
          <button className="pk-close" onClick={onCancel} aria-label="닫기">
            <Icons.X s={14} />
          </button>
        </div>
        <div className="confirm-body">{message}</div>
        <div className="confirm-actions">
          <button className="confirm-btn cancel" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            className={`confirm-btn ${variant === "danger" ? "danger" : "primary"}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
