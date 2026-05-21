import { useMemo } from "react";

interface CodeBlockProps {
  readonly lang: string;
  readonly code: string;
}

export function CodeBlock({ lang, code }: CodeBlockProps) {
  const tokens = useMemo(() => tokenize(code), [code]);

  return (
    <pre className="code">
      {lang && <span className="lang">{lang}</span>}
      <code>
        {tokens.map((t, i) =>
          t.cls ? (
            <span key={i} className={t.cls}>
              {t.text}
            </span>
          ) : (
            t.text
          ),
        )}
      </code>
    </pre>
  );
}

interface Token {
  readonly text: string;
  readonly cls: string;
}

function tokenize(code: string): readonly Token[] {
  const result: Token[] = [];
  const regex =
    /(\/\/.*$|#.*$)|(["'`](?:[^"'`\\]|\\.)*["'`])|(\b\d[\d.]*\b)|(\b(?:const|let|var|function|return|if|else|import|export|from|class|def|async|await|for|while|in|of|type|interface|readonly|true|false|null|undefined|new|this|try|catch|throw|switch|case|break|continue|yield|with|as|is)\b)/gm;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(code)) !== null) {
    if (match.index > lastIndex) {
      result.push({ text: code.slice(lastIndex, match.index), cls: "" });
    }
    if (match[1]) result.push({ text: match[1], cls: "c" });
    else if (match[2]) result.push({ text: match[2], cls: "s" });
    else if (match[3]) result.push({ text: match[3], cls: "n" });
    else if (match[4]) result.push({ text: match[4], cls: "k" });
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < code.length) {
    result.push({ text: code.slice(lastIndex), cls: "" });
  }

  return result;
}
