import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { usePipelineActions } from "../../hooks/use-pipeline-actions";
import { MarkdownRenderer } from "../editor/MarkdownRenderer";
import { api } from "../../api/client";

interface ContentPreviewProps {
  runId: number;
}

export function ContentPreview({ runId }: ContentPreviewProps) {
  const articleContent = useAppStore((s) => s.articleContent);
  const activeArticle = useAppStore((s) => s.activeArticle);
  const setArticleContent = useAppStore((s) => s.setArticleContent);
  const validationSummary = usePipelineStore((s) => s.validationSummary);
  const { fetchValidations } = usePipelineActions();

  useEffect(() => {
    void fetchValidations(runId);
  }, [runId, fetchValidations]);

  useEffect(() => {
    if (!articleContent && activeArticle) {
      void api.articles.getContent(activeArticle.id).then((content) => {
        if (content) setArticleContent(content);
      });
    }
  }, [activeArticle, articleContent, setArticleContent]);

  return (
    <div className="space-y-4">
      {/* Validation summary */}
      {validationSummary && (
        <div className="flex gap-3">
          <SummaryBadge
            label="PASS"
            count={validationSummary.passed}
            color="var(--color-success)"
          />
          <SummaryBadge
            label="FAIL"
            count={validationSummary.failed}
            color="var(--color-danger)"
          />
          <div
            className="flex items-center text-xs"
            style={{ color: "var(--color-text-faint)" }}
          >
            점수 {Math.round(validationSummary.score * 100)}%
          </div>
        </div>
      )}

      {/* Notice */}
      <div
        className="text-xs px-3 py-2 rounded-md"
        style={{
          backgroundColor: "color-mix(in oklch, var(--color-warn) 10%, transparent)",
          color: "var(--color-warn)",
        }}
      >
        이 게이트는 절대 자동화하지 않습니다. 실제로 발행할지 사람이 결정합니다.
      </div>

      {/* Content preview */}
      <div
        className="max-h-96 overflow-y-auto rounded-md border p-4"
        style={{
          borderColor: "var(--color-border)",
          backgroundColor: "var(--color-bg-elev)",
        }}
      >
        {articleContent ? (
          <MarkdownRenderer content={articleContent} />
        ) : (
          <p style={{ color: "var(--color-text-faint)" }}>
            콘텐츠를 불러오는 중...
          </p>
        )}
      </div>
    </div>
  );
}

function SummaryBadge({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div
      className="px-3 py-1.5 rounded-md text-center"
      style={{ backgroundColor: "var(--color-bg-sub)" }}
    >
      <div className="text-base font-semibold" style={{ color }}>
        {count}
      </div>
      <div
        className="text-xs"
        style={{ color: "var(--color-text-faint)" }}
      >
        {label}
      </div>
    </div>
  );
}
