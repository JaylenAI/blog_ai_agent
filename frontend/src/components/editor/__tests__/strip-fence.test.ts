import { describe, it, expect } from "vitest";
import { stripWrappingCodeFence } from "../strip-fence";

describe("stripWrappingCodeFence", () => {
  it("```markdown 으로 감싼 본문의 바깥 펜스를 제거한다", () => {
    const text = "```markdown\n## 제목\n\n본문입니다.\n```";
    expect(stripWrappingCodeFence(text)).toBe("## 제목\n\n본문입니다.");
  });

  it("언어 없는 ``` 래핑도 제거한다", () => {
    const text = "```\n## 제목\n본문\n```";
    expect(stripWrappingCodeFence(text)).toBe("## 제목\n본문");
  });

  it("바깥 펜스를 벗기되 본문 안의 코드블록은 유지한다", () => {
    const text = "```markdown\n## 제목\n\n```bash\nls -l\n```\n\n끝.\n```";
    const result = stripWrappingCodeFence(text);
    expect(result.startsWith("## 제목")).toBe(true);
    expect(result).toContain("```bash\nls -l\n```");
    expect(result.startsWith("```markdown")).toBe(false);
  });

  it("진짜 코드블록(bash 등)은 건드리지 않는다", () => {
    const text = "```bash\nls -l\n```";
    expect(stripWrappingCodeFence(text)).toBe(text);
  });

  it("펜스가 없으면 원본 그대로 반환한다", () => {
    const text = "## 제목\n\n그냥 본문입니다.";
    expect(stripWrappingCodeFence(text)).toBe(text);
  });

  it("이중 래핑도 모두 벗긴다", () => {
    const text = "```markdown\n```markdown\n## 제목\n```\n```";
    expect(stripWrappingCodeFence(text)).toBe("## 제목");
  });

  it("본문 일부만 펜스인 경우(전체를 감싸지 않음)는 그대로 둔다", () => {
    const text = "앞 문단\n\n```bash\nls\n```\n\n뒤 문단";
    expect(stripWrappingCodeFence(text)).toBe(text);
  });
});
