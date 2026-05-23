import { Suspense, lazy } from "react";

const MarkdownRenderer = lazy(() =>
  import("./MarkdownRenderer").then((m) => ({ default: m.MarkdownRenderer })),
);

export function LazyMarkdownRenderer({
  content,
  articleId,
}: {
  content: string;
  articleId?: number;
}) {
  return (
    <Suspense
      fallback={
        <div
          style={{
            padding: "2rem",
            color: "var(--text-muted)",
            fontSize: 13,
          }}
        >
          마크다운 렌더러 로딩 중...
        </div>
      }
    >
      <MarkdownRenderer content={content} articleId={articleId} />
    </Suspense>
  );
}
