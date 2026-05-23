import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConfirmModal } from "../common/ConfirmModal";

describe("ConfirmModal", () => {
  const defaultProps = {
    title: "삭제 확인",
    message: "정말 삭제하시겠습니까?",
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it("renders title and message", () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText("삭제 확인")).toBeTruthy();
    expect(screen.getByText("정말 삭제하시겠습니까?")).toBeTruthy();
  });

  it("renders default button labels", () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByText("확인")).toBeTruthy();
    expect(screen.getByText("취소")).toBeTruthy();
  });

  it("renders custom button labels", () => {
    render(
      <ConfirmModal
        {...defaultProps}
        confirmLabel="삭제"
        cancelLabel="돌아가기"
      />,
    );
    expect(screen.getByText("삭제")).toBeTruthy();
    expect(screen.getByText("돌아가기")).toBeTruthy();
  });

  it("calls onConfirm when confirm button clicked", () => {
    const onConfirm = vi.fn();
    render(<ConfirmModal {...defaultProps} onConfirm={onConfirm} />);
    fireEvent.click(screen.getByText("확인"));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onCancel when cancel button clicked", () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(screen.getByText("취소"));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("calls onCancel on Escape key", () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("calls onCancel when overlay clicked", () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(document.querySelector(".confirm-overlay")!);
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("does not call onCancel when modal body clicked", () => {
    const onCancel = vi.fn();
    render(<ConfirmModal {...defaultProps} onCancel={onCancel} />);
    fireEvent.click(document.querySelector(".confirm-modal")!);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("has dialog role and aria attributes", () => {
    render(<ConfirmModal {...defaultProps} />);
    const dialog = document.querySelector("[role='dialog']");
    expect(dialog).toBeTruthy();
    expect(dialog?.getAttribute("aria-modal")).toBe("true");
    expect(dialog?.getAttribute("aria-labelledby")).toBe("confirm-modal-title");
  });

  it("applies danger variant class", () => {
    render(<ConfirmModal {...defaultProps} variant="danger" />);
    const confirmBtn = screen.getByText("확인");
    expect(confirmBtn.className).toContain("danger");
  });

  it("close button has aria-label", () => {
    render(<ConfirmModal {...defaultProps} />);
    expect(screen.getByLabelText("닫기")).toBeTruthy();
  });
});
