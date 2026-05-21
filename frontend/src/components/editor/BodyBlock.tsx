import { Inline } from "./Inline";
import { CodeBlock } from "./CodeBlock";
import { Figure } from "./Figure";

export type Block =
  | { readonly type: "p"; readonly text: string }
  | { readonly type: "h3"; readonly text: string }
  | { readonly type: "aeo-def"; readonly text: string }
  | {
      readonly type: "callout";
      readonly variant: "tip" | "warn" | "fire" | "info";
      readonly icon: string;
      readonly text: string;
    }
  | {
      readonly type: "table";
      readonly headers: readonly string[];
      readonly rows: readonly (readonly string[])[];
    }
  | { readonly type: "code"; readonly lang: string; readonly code: string }
  | {
      readonly type: "figure";
      readonly kind: "mmd" | "svg";
      readonly caption: string;
      readonly alt?: string;
    }
  | { readonly type: "refs"; readonly chips: readonly string[] };

interface BodyBlockProps {
  readonly block: Block;
}

export function BodyBlock({ block }: BodyBlockProps) {
  switch (block.type) {
    case "p":
      return (
        <p>
          <Inline text={block.text} />
        </p>
      );
    case "h3":
      return (
        <h3>
          <Inline text={block.text} />
        </h3>
      );
    case "aeo-def":
      return (
        <div className="aeo-def">
          <Inline text={block.text} />
        </div>
      );
    case "callout":
      return (
        <div className={`callout ${block.variant}`}>
          <span className="ico">{block.icon}</span>
          <div>
            <Inline text={block.text} />
          </div>
        </div>
      );
    case "table":
      return (
        <table className="cmp">
          <thead>
            <tr>
              {block.headers.map((h, i) => (
                <th key={i}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, ri) => (
              <tr key={ri}>
                {row.map((cell, ci) => (
                  <td key={ci} className={classifyCell(cell)}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    case "code":
      return <CodeBlock lang={block.lang} code={block.code} />;
    case "figure":
      return (
        <Figure kind={block.kind} caption={block.caption} alt={block.alt} />
      );
    case "refs":
      return (
        <div className="refs-inline">
          {block.chips.map((c, i) => (
            <span key={i} className="ref-chip">
              {c}
            </span>
          ))}
        </div>
      );
  }
}

function classifyCell(text: string): string {
  const trimmed = text.trim();
  if (/^[Oo✓✔]$/.test(trimmed)) return "ok";
  if (/^[Xx✗✘]$/.test(trimmed)) return "no";
  if (/^\d[\d,.]*$/.test(trimmed)) return "num";
  return "";
}
