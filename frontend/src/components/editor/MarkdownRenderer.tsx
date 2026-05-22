import { memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { Components } from "react-markdown";
import "../../styles/markdown.css";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

interface MarkdownRendererProps {
  content: string;
  articleId?: number;
}

function buildComponents(articleId?: number): Partial<Components> {
  return {
    a({ children, href }) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      );
    },
    table({ children }) {
      return (
        <div style={{ overflowX: "auto" }}>
          <table>{children}</table>
        </div>
      );
    },
    img({ src, alt }) {
      let resolvedSrc = src ?? "";
      if (articleId && resolvedSrc.startsWith("images/")) {
        const filename = resolvedSrc.slice("images/".length);
        resolvedSrc = `${BASE_URL}/articles/${articleId}/images/${encodeURIComponent(filename)}`;
      }
      return (
        <img
          src={resolvedSrc}
          alt={alt ?? ""}
          loading="lazy"
          style={{
            maxWidth: "100%",
            height: "auto",
            borderRadius: "var(--radius)",
            margin: "1rem 0",
          }}
        />
      );
    },
  };
}

export const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  articleId,
}: MarkdownRendererProps) {
  const components = useMemo(() => buildComponents(articleId), [articleId]);

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
