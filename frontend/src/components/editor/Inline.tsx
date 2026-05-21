import { useMemo } from "react";

interface InlineProps {
  readonly text: string;
}

interface InlineNode {
  readonly type: "text" | "bold" | "code";
  readonly value: string;
}

export function Inline({ text }: InlineProps) {
  const nodes = useMemo(() => parseInline(text), [text]);

  return (
    <>
      {nodes.map((node, i) => {
        switch (node.type) {
          case "bold":
            return <strong key={i}>{node.value}</strong>;
          case "code":
            return (
              <code
                key={i}
                style={{
                  fontFamily: "var(--font-mono)",
                  fontSize: "0.875em",
                  background: "var(--bg-sub)",
                  padding: "0.15em 0.35em",
                  borderRadius: "var(--radius-xs)",
                }}
              >
                {node.value}
              </code>
            );
          default:
            return <span key={i}>{node.value}</span>;
        }
      })}
    </>
  );
}

function parseInline(text: string): readonly InlineNode[] {
  const result: InlineNode[] = [];
  const regex = /(\*\*(.+?)\*\*)|(`(.+?)`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push({ type: "text", value: text.slice(lastIndex, match.index) });
    }
    if (match[1]) {
      result.push({ type: "bold", value: match[2] ?? "" });
    } else if (match[3]) {
      result.push({ type: "code", value: match[4] ?? "" });
    }
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    result.push({ type: "text", value: text.slice(lastIndex) });
  }

  return result;
}
