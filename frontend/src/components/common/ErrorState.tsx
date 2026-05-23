interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  message = "데이터를 불러올 수 없습니다.",
  onRetry,
  className = "",
}: ErrorStateProps) {
  return (
    <div className={`error-state ${className}`} role="alert">
      <span className="error-state-msg">{message}</span>
      {onRetry && (
        <button className="error-state-retry" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
}
