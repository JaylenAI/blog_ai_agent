import { useEffect, useState } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { api } from "../../api/client";
import type { ReferenceItem } from "../../types/publish";
import { Icons } from "../common/Icons";

function safeHostname(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function ReferencesTab() {
  const selectedArticleId = useAppStore((s) => s.activeArticle?.id);
  const events = usePipelineStore((s) => s.events);
  const [references, setReferences] = useState<ReferenceItem[]>([]);
  const [loading, setLoading] = useState(false);

  const sseReferences = (() => {
    const researchEvent = events.find(
      (e) => e.event_type === "stage_complete" && e.stage === "researcher",
    );
    return (researchEvent?.data?.references ?? []) as ReferenceItem[];
  })();

  useEffect(() => {
    if (sseReferences.length > 0) {
      setReferences(sseReferences);
      return;
    }
    if (!selectedArticleId) return;

    let cancelled = false;
    setLoading(true);
    api.articles
      .getReferences(selectedArticleId)
      .then((res) => {
        if (!cancelled && res.data) setReferences(res.data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedArticleId, sseReferences.length]);

  if (loading) {
    return <div className="empty">자료 로딩 중...</div>;
  }

  if (references.length === 0) {
    return (
      <div className="empty">
        파이프라인 실행 후 자료가 표시됩니다
      </div>
    );
  }

  const getRelevanceClass = (score: number) => {
    const r = Math.round(score * 5);
    if (r >= 5) return "r5";
    if (r >= 4) return "r4";
    return "r3";
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          marginBottom: 10,
          fontSize: 12,
          color: "var(--text-muted)",
        }}
      >
        <span>
          총{" "}
          <strong style={{ color: "var(--text)" }}>
            {references.length}건
          </strong>{" "}
          확보 · 최소 기준 8건 충족
        </span>
      </div>
      {references.map((r, i) => (
        <a
          key={i}
          className="ref-row"
          href={r.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            textDecoration: "none",
            color: "inherit",
            display: "flex",
          }}
        >
          <div
            className={`ref-rel ${getRelevanceClass(r.relevance_score)}`}
          >
            {Math.round(r.relevance_score * 5)}
          </div>
          <div className="ref-body">
            <div className="ref-title">{r.title}</div>
            <div className="ref-source">
              <span className="ref-type">{r.source_type}</span>
              <span>{safeHostname(r.url)}</span>
              <Icons.ExternalLink s={10} />
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}
