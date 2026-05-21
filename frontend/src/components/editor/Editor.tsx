import type { Article } from "../../types/article";
import { useAppStore } from "../../stores/app-store";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface EditorProps {
  article: Article;
}

export function Editor({ article }: EditorProps) {
  const pipelineMode = useAppStore((s) => s.pipelineMode);
  const articleContent = useAppStore((s) => s.articleContent);

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Category badge */}
        {article.category && (
          <span
            className="text-xs px-2 py-0.5 rounded font-medium"
            style={{
              backgroundColor: "var(--color-bg-sub)",
              color: "var(--color-accent)",
            }}
          >
            {article.category}
          </span>
        )}

        {/* Title */}
        <h1
          className="text-3xl font-semibold leading-snug"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {article.title ?? article.topic}
        </h1>

        {/* Meta bar */}
        <div
          className="flex gap-4 text-xs py-2 border-b"
          style={{
            color: "var(--color-text-faint)",
            borderColor: "var(--color-border)",
          }}
        >
          <span>
            {article.word_count > 0
              ? `${article.word_count.toLocaleString()}자`
              : "분량 미정"}
          </span>
          <span>이미지 {article.image_count}장</span>
          <span>상태: {article.status}</span>
        </div>

        {/* Content */}
        {articleContent ? (
          <MarkdownRenderer content={articleContent} />
        ) : pipelineMode === "idle" ? (
          <p style={{ color: "var(--color-text-muted)" }}>
            파이프라인을 시작하면 이 영역에 콘텐츠가 생성됩니다.
          </p>
        ) : pipelineMode === "research" || pipelineMode === "outline" ? (
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className="rounded-md animate-pulse"
                style={{
                  backgroundColor: "var(--color-bg-sub)",
                  height: `${60 + (i % 3) * 20}px`,
                }}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="rounded-md animate-pulse"
                style={{
                  backgroundColor: "var(--color-bg-sub)",
                  height: `${40 + (i % 4) * 15}px`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
