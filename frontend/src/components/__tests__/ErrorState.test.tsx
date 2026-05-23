import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ErrorState } from "../common/ErrorState";

describe("ErrorState", () => {
  it("renders default message", () => {
    render(<ErrorState />);
    expect(screen.getByText("데이터를 불러올 수 없습니다.")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<ErrorState message="네트워크 오류" />);
    expect(screen.getByText("네트워크 오류")).toBeInTheDocument();
  });

  it("has alert role for accessibility", () => {
    render(<ErrorState />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    render(<ErrorState onRetry={() => {}} />);
    expect(screen.getByText("다시 시도")).toBeInTheDocument();
  });

  it("does not render retry button without onRetry", () => {
    render(<ErrorState />);
    expect(screen.queryByText("다시 시도")).not.toBeInTheDocument();
  });

  it("calls onRetry when retry button clicked", () => {
    const onRetry = vi.fn();
    render(<ErrorState onRetry={onRetry} />);
    fireEvent.click(screen.getByText("다시 시도"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("applies custom className", () => {
    const { container } = render(<ErrorState className="test-class" />);
    expect(container.firstChild).toHaveClass("test-class");
  });
});
