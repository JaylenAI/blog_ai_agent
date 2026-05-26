import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";

interface TistoryStatus {
  status: string;
  blog_url?: string;
  http_status?: number;
  message?: string;
}

export function TistoryPanel() {
  const [check, setCheck] = useState<TistoryStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.health.detailed();
      const tistory = res.data?.checks?.tistory;
      setCheck(tistory ?? { status: "unknown", message: "정보 없음" });
    } catch {
      setCheck({ status: "error", message: "서버 연결 실패" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const statusLabel = (s: string) => {
    switch (s) {
      case "ok": return "연결됨";
      case "warning": return "경고";
      case "error": return "오류";
      case "disabled": return "미설정";
      default: return "알 수 없음";
    }
  };

  const statusColor = (s: string) => {
    switch (s) {
      case "ok": return "var(--color-success, #22c55e)";
      case "warning": return "var(--color-warning, #f59e0b)";
      case "error": return "var(--color-error, #ef4444)";
      default: return "var(--color-text-tertiary, #888)";
    }
  };

  return (
    <div className="sb-panel-info">
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">블로그</span>
        <span>{check?.blog_url ?? "jaylenhan.tistory.com"}</span>
      </div>
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">연결 상태</span>
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: statusColor(check?.status ?? "unknown"),
              display: "inline-block",
            }}
            role="status"
            aria-label={`Tistory 연결 상태: ${statusLabel(check?.status ?? "unknown")}`}
          />
          {loading ? "확인 중..." : statusLabel(check?.status ?? "unknown")}
        </span>
      </div>
      {check?.http_status && (
        <div className="sb-panel-info-row">
          <span className="sb-panel-info-label">HTTP 상태</span>
          <span>{check.http_status}</span>
        </div>
      )}
      {check?.message && (
        <div className="sb-panel-info-row">
          <span className="sb-panel-info-label">메시지</span>
          <span style={{ fontSize: "0.85em", color: "var(--color-text-secondary)" }}>
            {check.message}
          </span>
        </div>
      )}
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">연결 방식</span>
        <span>Playwright (수동 로그인)</span>
      </div>
      <button
        className="sb-panel-btn"
        onClick={fetchStatus}
        disabled={loading}
        style={{
          marginTop: "8px",
          padding: "6px 12px",
          cursor: loading ? "wait" : "pointer",
          border: "1px solid var(--color-border)",
          borderRadius: "4px",
          background: "var(--color-bg-secondary, #f5f5f5)",
          fontSize: "0.85em",
          width: "100%",
        }}
      >
        {loading ? "확인 중..." : "연결 상태 새로고침"}
      </button>
      <p className="sb-panel-note" style={{ marginTop: "8px" }}>
        Tistory 발행은 Gate 2 승인 후 Playwright가 브라우저를 열어
        진행합니다. 카카오 로그인이 필요할 경우 수동으로 진행해 주세요.
      </p>
    </div>
  );
}
