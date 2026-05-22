import { memo, useEffect, useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import mermaid from "mermaid";
import type { Components } from "react-markdown";
import "../../styles/markdown.css";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    primaryColor: "#3b82f6",
    primaryTextColor: "#e2e8f0",
    primaryBorderColor: "#475569",
    lineColor: "#64748b",
    secondaryColor: "#1e293b",
    tertiaryColor: "#0f172a",
    fontFamily: "'Pretendard', sans-serif",
  },
});

interface MarkdownRendererProps {
  content: string;
  articleId?: number;
}

function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const id = `mermaid-${Math.random().toString(36).slice(2, 9)}`;
    mermaid
      .render(id, code)
      .then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg;
      })
      .catch(() => {
        if (ref.current) {
          ref.current.textContent = code;
          ref.current.style.whiteSpace = "pre";
        }
      });
  }, [code]);

  return (
    <div
      ref={ref}
      style={{
        display: "flex",
        justifyContent: "center",
        margin: "1.5rem 0",
        overflow: "auto",
      }}
    />
  );
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
    code({ className, children }) {
      const match = /language-(\w+)/.exec(className ?? "");
      const lang = match ? match[1] : "";
      const text = String(children).replace(/\n$/, "");

      if (lang === "mermaid") {
        return <MermaidBlock code={text} />;
      }

      return <code className={className}>{children}</code>;
    },
    pre({ children }) {
      return <pre>{children}</pre>;
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
        rehypePlugins={[rehypeRaw, rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});
