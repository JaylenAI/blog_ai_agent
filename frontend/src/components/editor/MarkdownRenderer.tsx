import { memo, useEffect, useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import rehypeRaw from "rehype-raw";
import mermaid from "mermaid";
import type { Components } from "react-markdown";
import { useUIStore } from "../../stores/ui-store";
import { stripWrappingCodeFence } from "./strip-fence";
import "../../styles/markdown.css";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

function initMermaidTheme(theme: "light" | "dark") {
  mermaid.initialize({
    startOnLoad: false,
    theme: theme === "dark" ? "dark" : "default",
    themeVariables:
      theme === "dark"
        ? {
            primaryColor: "#3b82f6",
            primaryTextColor: "#e2e8f0",
            primaryBorderColor: "#475569",
            lineColor: "#64748b",
            secondaryColor: "#1e293b",
            tertiaryColor: "#0f172a",
            fontFamily: "'Pretendard', sans-serif",
          }
        : {
            primaryColor: "#3b82f6",
            primaryTextColor: "#1e293b",
            primaryBorderColor: "#cbd5e1",
            lineColor: "#94a3b8",
            secondaryColor: "#f1f5f9",
            tertiaryColor: "#e2e8f0",
            fontFamily: "'Pretendard', sans-serif",
          },
  });
}

initMermaidTheme("dark");

interface MarkdownRendererProps {
  content: string;
  articleId?: number;
}

function MermaidBlock({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const theme = useUIStore((s) => s.theme);

  useEffect(() => {
    initMermaidTheme(theme);
  }, [theme]);

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
  }, [code, theme]);

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
  // 이미 ```markdown 으로 감싸여 저장된 글도 정상 렌더링되도록 방어한다.
  const cleaned = useMemo(() => stripWrappingCodeFence(content), [content]);

  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeHighlight]}
        components={components}
      >
        {cleaned}
      </ReactMarkdown>
    </div>
  );
});
