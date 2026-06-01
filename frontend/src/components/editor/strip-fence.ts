// 본문 전체를 감싼 코드펜스를 탐지한다. LLM이 마크다운 결과물을
// ```markdown ... ``` 또는 ``` ... ``` 으로 한 번 더 감싸는 경우를 교정한다.
const WRAPPING_FENCE = /^\s*```[ \t]*([A-Za-z0-9_-]*)[ \t]*\r?\n([\s\S]*?)\r?\n```[ \t]*\s*$/;

// 벗겨낼 언어 토큰 — bash 등 진짜 코드블록은 건드리지 않는다.
const LANGS_TO_STRIP = new Set(["", "markdown", "md", "mdx"]);

/**
 * 본문 전체를 감싼 불필요한 코드펜스를 제거한다.
 * 바깥 펜스가 본문을 통째로 감쌀 때만 제거하며, 본문 중간의 정상
 * 코드블록(```bash 등)은 그대로 둔다. 이미 오염되어 저장된 글도
 * 화면에서는 정상 렌더링되도록 하는 방어 로직이다.
 */
export function stripWrappingCodeFence(text: string): string {
  if (!text.includes("```")) return text;

  const match = WRAPPING_FENCE.exec(text.trim());
  if (match === null) return text;

  const [, langGroup, innerGroup] = match;
  if (innerGroup === undefined) return text;

  const lang = (langGroup ?? "").toLowerCase();
  if (!LANGS_TO_STRIP.has(lang)) return text;

  // 안쪽이 또 다른 단일 래핑 펜스면 한 번 더 처리(이중 래핑 방지).
  return stripWrappingCodeFence(innerGroup);
}
