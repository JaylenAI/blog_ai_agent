import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { Icons } from "../common/Icons";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { ErrorState } from "../common/ErrorState";

interface VersionEntry {
  version_id: string;
  timestamp: string;
  size: number;
  word_count: number;
}

export function HistoryTab() {
  const activeArticle = useAppStore((s) => s.activeArticle);
  const setArticleContent = useAppStore((s) => s.setArticleContent);
  const addToast = useAppStore((s) => s.addToast);
  const [versions, setVersions] = useState<VersionEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetchError, setFetchError] = useState(false);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [previewContent, setPreviewContent] = useState<string | null>(
    null,
  );

  const fetchVersions = useCallback(async () => {
    if (!activeArticle) return;
    setLoading(true);
    setFetchError(false);
    try {
      const res = await api.articles.listVersions(activeArticle.id);
      if (res.success && res.data) {
        setVersions(res.data as VersionEntry[]);
      }
    } catch {
      setFetchError(true);
    } finally {
      setLoading(false);
    }
  }, [activeArticle]);

  useEffect(() => {
    void fetchVersions();
  }, [fetchVersions]);

  const handlePreview = useCallback(
    async (versionId: string) => {
      if (!activeArticle) return;
      if (previewId === versionId) {
        setPreviewId(null);
        setPreviewContent(null);
        return;
      }
      try {
        const content = await api.articles.getVersionContent(
          activeArticle.id,
          versionId,
        );
        setPreviewId(versionId);
        setPreviewContent(content);
      } catch {
        addToast({ type: "error", message: "버전 미리보기 로드 실패" });
      }
    },
    [activeArticle, previewId],
  );

  const handleRestore = useCallback(
    async (versionId: string) => {
      if (!activeArticle) return;
      try {
        const res = await api.articles.restoreVersion(
          activeArticle.id,
          versionId,
        );
        if (res.success) {
          const content = await api.articles.getContent(
            activeArticle.id,
          );
          if (content) setArticleContent(content);
          addToast({ type: "success", message: "버전 복원 완료" });
          void fetchVersions();
        }
      } catch {
        addToast({ type: "error", message: "복원 실패" });
      }
    },
    [activeArticle, setArticleContent, addToast, fetchVersions],
  );

  if (!activeArticle) {
    return <div className="empty">아티클을 선택해 주세요</div>;
  }

  if (loading) {
    return <LoadingSpinner message="버전 이력 불러오는 중..." />;
  }

  if (fetchError) {
    return <ErrorState message="버전 이력을 불러올 수 없습니다." onRetry={fetchVersions} />;
  }

  if (versions.length === 0) {
    return (
      <div className="empty">
        저장된 버전이 없습니다. 편집 후 저장하면 자동으로
        백업됩니다.
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          fontSize: 12,
          color: "var(--text-muted)",
          marginBottom: 10,
        }}
      >
        총{" "}
        <strong style={{ color: "var(--text)" }}>
          {versions.length}개
        </strong>{" "}
        버전 (최대 10개 보관)
      </div>
      {versions.map((v) => (
        <div key={v.version_id} className="history-row">
          <div className="history-info">
            <div className="history-time">{v.timestamp}</div>
            <div className="history-meta">
              {v.word_count.toLocaleString()}자 ·{" "}
              {(v.size / 1024).toFixed(1)}KB
            </div>
          </div>
          <div className="history-actions">
            <button
              className="history-btn"
              onClick={() => handlePreview(v.version_id)}
              title="미리보기"
            >
              <Icons.Eye s={11} />
            </button>
            <button
              className="history-btn restore"
              onClick={() => handleRestore(v.version_id)}
              title="이 버전으로 복원"
            >
              복원
            </button>
          </div>
          {previewId === v.version_id && previewContent && (
            <pre className="history-preview">
              {previewContent.slice(0, 500)}...
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
