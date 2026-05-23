import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LoadingSpinner } from "../common/LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders default message", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText("불러오는 중...")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<LoadingSpinner message="데이터 로딩 중..." />);
    expect(screen.getByText("데이터 로딩 중...")).toBeInTheDocument();
  });

  it("has status role for accessibility", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<LoadingSpinner className="custom" />);
    expect(container.firstChild).toHaveClass("custom");
  });

  it("renders spinner element", () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector(".spinner")).toBeInTheDocument();
  });
});
