import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { LoadingSpinner } from "../common/LoadingSpinner";
import { ErrorState } from "../common/ErrorState";

export function StyleGuidePanel() {
  const [content, setContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchGuide = useCallback(() => {
    setLoading(true);
    setError(false);
    api.settings
      .getStyleGuide()
      .then((text) => setContent(text))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchGuide();
  }, [fetchGuide]);

  if (loading) return <LoadingSpinner message="스타일 가이드 불러오는 중..." />;
  if (error) return <ErrorState message="스타일 가이드를 불러올 수 없습니다." onRetry={fetchGuide} />;

  return (
    <pre className="sb-panel-pre">
      {content ?? "파일을 찾을 수 없습니다."}
    </pre>
  );
}
