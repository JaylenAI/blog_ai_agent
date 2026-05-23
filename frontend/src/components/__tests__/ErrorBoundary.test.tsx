import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorBoundary } from "../common/ErrorBoundary";

function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error("테스트 오류");
  return <div>정상 렌더링</div>;
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders children when no error", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("정상 렌더링")).toBeTruthy();
  });

  it("renders default error UI when error occurs", () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("오류가 발생했습니다")).toBeTruthy();
    expect(screen.getByText("페이지를 표시하는 중 문제가 발생했습니다. 다시 시도해 주세요.")).toBeTruthy();
  });

  it("renders custom fallback when provided", () => {
    render(
      <ErrorBoundary fallback={<div>커스텀 에러</div>}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("커스텀 에러")).toBeTruthy();
  });

  it("retry button resets error state", () => {
    let shouldThrow = true;
    function Conditional() {
      if (shouldThrow) throw new Error("테스트 오류");
      return <div>정상 렌더링</div>;
    }

    render(
      <ErrorBoundary>
        <Conditional />
      </ErrorBoundary>,
    );
    expect(screen.getByText("다시 시도")).toBeTruthy();

    shouldThrow = false;
    fireEvent.click(screen.getByText("다시 시도"));
    expect(screen.getByText("정상 렌더링")).toBeTruthy();
  });
});
