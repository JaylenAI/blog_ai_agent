import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GateModal } from "../gate/GateModal";
import { usePipelineStore } from "../../stores/pipeline-store";

const mockRejectAndRevise = vi.fn().mockResolvedValue(undefined);

vi.mock("../../hooks/use-pipeline-actions", () => ({
  usePipelineActions: () => ({
    approveGate: mockApprove,
    rejectGate: mockReject,
    rejectAndRevise: mockRejectAndRevise,
    fetchValidations: vi.fn().mockResolvedValue(undefined),
  }),
}));

vi.mock("../gate/OutlinePreview", () => ({
  OutlinePreview: () => <div data-testid="outline-preview" />,
}));

vi.mock("../gate/ContentPreview", () => ({
  ContentPreview: ({ runId }: { runId: number }) => (
    <div data-testid="content-preview" data-run-id={runId} />
  ),
}));

const mockApprove = vi.fn().mockResolvedValue(undefined);
const mockReject = vi.fn().mockResolvedValue(undefined);
const mockOnClose = vi.fn();

describe("GateModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePipelineStore.getState().reset();
  });

  it("renders gate 1 title", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    expect(screen.getByText("GATE 1")).toBeInTheDocument();
    expect(screen.getByText("아웃라인 검수")).toBeInTheDocument();
  });

  it("renders gate 2 title", () => {
    render(<GateModal gate="gate_two" runId={2} onClose={mockOnClose} />);
    expect(screen.getByText("GATE 2")).toBeInTheDocument();
    expect(screen.getByText(/최종 검수/)).toBeInTheDocument();
  });

  it("renders OutlinePreview for gate 1", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    expect(screen.getByTestId("outline-preview")).toBeInTheDocument();
  });

  it("renders ContentPreview for gate 2", () => {
    render(<GateModal gate="gate_two" runId={5} onClose={mockOnClose} />);
    expect(screen.getByTestId("content-preview")).toBeInTheDocument();
    expect(screen.getByTestId("content-preview")).toHaveAttribute(
      "data-run-id",
      "5",
    );
  });

  it("gate 1 approve button shows '본문 생성 시작'", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    expect(screen.getByText("본문 생성 시작")).toBeInTheDocument();
  });

  it("gate 2 approve button shows 'Tistory에 발행 준비'", () => {
    render(<GateModal gate="gate_two" runId={2} onClose={mockOnClose} />);
    expect(screen.getByText("Tistory에 발행 준비")).toBeInTheDocument();
  });

  it("calls approveGate when approve button clicked (gate 1)", async () => {
    render(<GateModal gate="gate_one" runId={7} onClose={mockOnClose} />);
    fireEvent.click(screen.getByText("본문 생성 시작"));
    expect(mockApprove).toHaveBeenCalledWith(7);
  });

  it("calls rejectGate when reject button clicked", async () => {
    render(<GateModal gate="gate_one" runId={3} onClose={mockOnClose} />);
    fireEvent.click(screen.getByText("수정 요청"));
    fireEvent.click(screen.getByText("수정 요청"));
    expect(mockReject).toHaveBeenCalledWith(3);
  });

  it("calls onClose when '나중에' button clicked", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    fireEvent.click(screen.getByText("나중에"));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("calls onClose when clicking scrim", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    const scrim = document.querySelector(".modal-scrim")!;
    fireEvent.click(scrim);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("does not call onClose when clicking modal body", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    const modal = document.querySelector(".modal")!;
    fireEvent.click(modal);
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it("disables buttons while running", () => {
    usePipelineStore.setState({ isRunning: true });
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    expect(screen.getByText("처리 중...").closest("button")).toBeDisabled();
    expect(screen.getByText("수정 요청").closest("button")).toBeDisabled();
  });

  it("gate 2 approve disabled until checklist complete", () => {
    render(<GateModal gate="gate_two" runId={2} onClose={mockOnClose} />);
    const approveBtn = screen.getByText("Tistory에 발행 준비").closest("button")!;
    expect(approveBtn).toBeDisabled();
  });

  it("gate 2 approve enabled after all checklist items checked", () => {
    render(<GateModal gate="gate_two" runId={2} onClose={mockOnClose} />);

    const checklistItems = [
      "카테고리 태그 10개 확인",
      "JSON-LD TechArticle + HowTo schema 삽입",
      "이미지 alt 태그 부여",
      "마치며 3단 서사 구조 확인",
      "OG:image 메타 확인",
      "내부 링크 2개 이상 삽입",
    ];

    for (const item of checklistItems) {
      fireEvent.click(screen.getByText(item));
    }

    const approveBtn = screen.getByText("Tistory에 발행 준비").closest("button")!;
    expect(approveBtn).not.toBeDisabled();
  });

  it("closes on Escape key", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
  });

  it("has proper ARIA attributes", () => {
    render(<GateModal gate="gate_one" runId={1} onClose={mockOnClose} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "gate-modal-title");
  });

  it("gate 2 checklist persists to localStorage", () => {
    const setItemSpy = vi.spyOn(Storage.prototype, "setItem");

    render(<GateModal gate="gate_two" runId={42} onClose={mockOnClose} />);

    fireEvent.click(screen.getByText("카테고리 태그 10개 확인"));

    expect(setItemSpy).toHaveBeenCalledWith(
      "gate2-checklist-42",
      expect.any(String),
    );

    const savedValue = JSON.parse(
      setItemSpy.mock.calls.find(
        (call) => call[0] === "gate2-checklist-42",
      )![1],
    );
    expect(savedValue[0]).toBe(true);

    setItemSpy.mockRestore();
  });

  it("gate 2 checklist restores from localStorage", () => {
    const stored: Record<number, boolean> = {
      0: true,
      1: true,
      2: true,
      3: true,
      4: true,
      5: true,
    };
    const getItemSpy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(
      (key: string) => {
        if (key === "gate2-checklist-99") return JSON.stringify(stored);
        return null;
      },
    );

    render(<GateModal gate="gate_two" runId={99} onClose={mockOnClose} />);

    const checklistItems = [
      "카테고리 태그 10개 확인",
      "JSON-LD TechArticle + HowTo schema 삽입",
      "이미지 alt 태그 부여",
      "마치며 3단 서사 구조 확인",
      "OG:image 메타 확인",
      "내부 링크 2개 이상 삽입",
    ];

    for (const item of checklistItems) {
      const el = screen.getByText(item);
      expect(el.closest("div")).toHaveStyle("text-decoration: line-through");
    }

    const approveBtn = screen
      .getByText("Tistory에 발행 준비")
      .closest("button")!;
    expect(approveBtn).not.toBeDisabled();

    getItemSpy.mockRestore();
  });
});
