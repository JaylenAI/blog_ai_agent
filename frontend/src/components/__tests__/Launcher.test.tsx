import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Launcher } from "../editor/Launcher";

vi.mock("../../api/client", () => ({
  api: {
    formats: {
      list: vi.fn().mockResolvedValue({ data: [] }),
      suggest: vi.fn().mockResolvedValue({ data: [] }),
    },
  },
}));

describe("Launcher", () => {
  const mockOnStart = vi.fn();

  beforeEach(() => {
    mockOnStart.mockClear();
  });

  it("renders heading and input", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    expect(screen.getByText("오늘은 어떤 주제로 쓸까요?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/에이전틱 RAG/)).toBeInTheDocument();
  });

  it("submit button is disabled when input is empty", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    const submitBtn = screen.getByText("생성 시작").closest("button")!;
    expect(submitBtn).toBeDisabled();
  });

  it("submit button is enabled when input has text", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    const textarea = screen.getByPlaceholderText(/에이전틱 RAG/);
    fireEvent.change(textarea, { target: { value: "테스트 주제" } });
    const submitBtn = screen.getByText("생성 시작").closest("button")!;
    expect(submitBtn).not.toBeDisabled();
  });

  it("calls onStart when submit is clicked", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    const textarea = screen.getByPlaceholderText(/에이전틱 RAG/);
    fireEvent.change(textarea, { target: { value: "테스트 주제" } });
    const submitBtn = screen.getByText("생성 시작").closest("button")!;
    fireEvent.click(submitBtn);
    expect(mockOnStart).toHaveBeenCalledWith("테스트 주제", expect.any(Boolean), expect.any(String), expect.any(String));
  });

  it("disables everything when disabled prop is true", () => {
    render(<Launcher onStart={mockOnStart} disabled={true} />);
    const textarea = screen.getByPlaceholderText(/에이전틱 RAG/);
    expect(textarea).toBeDisabled();
  });

  it("renders suggestion cards", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    expect(screen.getByText("에이전틱 RAG 완벽 가이드 2026")).toBeInTheDocument();
    expect(screen.getByText("MCP 서버 직접 구축하기")).toBeInTheDocument();
  });

  it("clicking suggestion card calls onStart with card title", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    const card = screen.getByText("MCP 서버 직접 구축하기").closest("button")!;
    fireEvent.click(card);
    expect(mockOnStart).toHaveBeenCalledWith("MCP 서버 직접 구축하기", expect.any(Boolean), "tutorial", expect.any(String));
  });

  it("renders auto format button", () => {
    render(<Launcher onStart={mockOnStart} disabled={false} />);
    expect(screen.getByText("자동")).toBeInTheDocument();
  });
});
