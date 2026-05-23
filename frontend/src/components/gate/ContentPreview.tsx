import { useEffect } from "react";
import { useAppStore } from "../../stores/app-store";
import { usePipelineActions } from "../../hooks/use-pipeline-actions";
import { LazyMarkdownRenderer as MarkdownRenderer } from "../editor/LazyMarkdownRenderer";
import { api } from "../../api/client";

interface ContentPreviewProps {
  runId: number;
}

export function ContentPreview({ runId }: ContentPreviewProps) {
  const articleContent = useAppStore((s) => s.articleContent);
  const activeArticle = useAppStore((s) => s.activeArticle);
  const setArticleContent = useAppStore((s) => s.setArticleContent);
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
    <div
      style={{
        maxHeight: 384,
        overflowY: "auto",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius)",
        padding: 16,
        background: "var(--bg-elev)",
      }}
    >
      {articleContent ? (
        <MarkdownRenderer content={articleContent} />
      ) : (
        <p style={{ color: "var(--text-faint)" }}>콘텐츠를 불러오는 중...</p>
      )}
    </div>
  );
}
