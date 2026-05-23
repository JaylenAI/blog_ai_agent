import { useCallback, useEffect, useState } from "react";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { ErrorState } from "../common/ErrorState";

interface HealthCheck {
  status: string;
  path?: string;
  version?: string;
  message?: string;
}

interface HealthData {
  status: string;
  checks: {
    database?: HealthCheck;
    claude_cli?: HealthCheck;
    mermaid_cli?: HealthCheck;
    obsidian_vault?: HealthCheck;
  };
}

function isOk(check?: HealthCheck): boolean {
  return check?.status === "ok";
}

function badgeClass(check?: HealthCheck): string {
  if (!check) return "inactive";
  if (check.status === "ok") return "active";
  if (check.status === "warning" || check.status === "disabled")
    return "inactive";
  return "inactive";
}

export function McpPanel() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchHealth = useCallback(() => {
    setLoading(true);
    setError(false);
    fetch("/api/v1/health/detailed")
      .then((r) => r.json())
      .then((d) => {
        const payload = d.data ?? d;
        setHealth(payload);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  if (loading) return <LoadingSpinner message="시스템 상태 확인 중..." />;
  if (error || !health) {
    return <ErrorState message="시스템 상태를 불러올 수 없습니다. 백엔드 서버가 실행 중인지 확인해 주세요." onRetry={fetchHealth} />;
  }

  const { checks } = health;

  return (
    <div className="sb-panel-info">
      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">Claude CLI</span>
        <span>
          {isOk(checks.claude_cli) ? (
            <span className="sp-status-badge active">
              {checks.claude_cli?.version ?? "connected"}
            </span>
          ) : (
            <span className="sp-status-badge inactive">
              {checks.claude_cli?.message ?? "unavailable"}
            </span>
          )}
        </span>
      </div>
      {checks.claude_cli?.path && (
        <div className="sb-panel-info-row">
          <span className="sb-panel-info-label">CLI 경로</span>
          <span
            style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}
          >
            {checks.claude_cli.path}
          </span>
        </div>
      )}

      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">Mermaid CLI</span>
        <span>
          <span
            className={`sp-status-badge ${badgeClass(checks.mermaid_cli)}`}
          >
            {isOk(checks.mermaid_cli) ? "ready" : "unavailable"}
          </span>
        </span>
      </div>
      {checks.mermaid_cli?.path && (
        <div className="sb-panel-info-row">
          <span className="sb-panel-info-label">mmdc 경로</span>
          <span
            style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}
          >
            {checks.mermaid_cli.path}
          </span>
        </div>
      )}

      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">Database</span>
        <span>
          <span
            className={`sp-status-badge ${badgeClass(checks.database)}`}
          >
            {checks.database?.status ?? "unknown"}
          </span>
        </span>
      </div>

      <div className="sb-panel-info-row">
        <span className="sb-panel-info-label">Obsidian Vault</span>
        <span>
          <span
            className={`sp-status-badge ${badgeClass(checks.obsidian_vault)}`}
          >
            {isOk(checks.obsidian_vault)
              ? "connected"
              : checks.obsidian_vault?.status ?? "unknown"}
          </span>
        </span>
      </div>
      {checks.obsidian_vault?.path && (
        <div className="sb-panel-info-row">
          <span className="sb-panel-info-label">Vault 경로</span>
          <span
            style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}
          >
            {checks.obsidian_vault.path}
          </span>
        </div>
      )}
    </div>
  );
}
