export const STATUS_DISPLAY: Record<string, { label: string; cls: string }> = {
  draft: { label: "초안", cls: "draft" },
  researching: { label: "자료수집", cls: "active" },
  outlining: { label: "아웃라인", cls: "active" },
  generating: { label: "생성 중", cls: "active" },
  validating: { label: "검증 중", cls: "active" },
  review: { label: "검수 대기", cls: "review" },
  published: { label: "발행 완료", cls: "done" },
  failed: { label: "실패", cls: "failed" },
};

export const STATUS_LABELS: Record<string, string> = {
  running: "실행 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소",
  paused: "일시정지",
};

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
