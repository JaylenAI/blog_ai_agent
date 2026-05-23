interface LoadingSpinnerProps {
  message?: string;
  className?: string;
}

export function LoadingSpinner({
  message = "불러오는 중...",
  className = "",
}: LoadingSpinnerProps) {
  return (
    <div className={`loading-spinner ${className}`} role="status">
      <div className="spinner" />
      <span>{message}</span>
    </div>
  );
}
