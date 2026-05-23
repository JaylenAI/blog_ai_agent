import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ToastContainer } from "../common/ToastContainer";
import { useToastStore } from "../../stores/toast-store";

describe("ToastContainer", () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it("renders nothing when no toasts", () => {
    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });

  it("renders toast messages", () => {
    useToastStore.getState().addToast({
      type: "success",
      message: "저장 완료",
    });

    render(<ToastContainer />);
    expect(screen.getByText("저장 완료")).toBeTruthy();
  });

  it("renders multiple toasts", () => {
    useToastStore.getState().addToast({
      type: "success",
      message: "첫번째",
    });
    useToastStore.getState().addToast({
      type: "error",
      message: "두번째",
    });

    render(<ToastContainer />);
    expect(screen.getByText("첫번째")).toBeTruthy();
    expect(screen.getByText("두번째")).toBeTruthy();
  });

  it("removes toast on close button click", async () => {
    useToastStore.getState().addToast({
      type: "info",
      message: "닫기 테스트",
    });

    render(<ToastContainer />);
    expect(screen.getByText("닫기 테스트")).toBeTruthy();

    const buttons = screen.getAllByRole("button");
    await userEvent.click(buttons[0]);

    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it("auto-dismisses after timeout", () => {
    vi.useFakeTimers();

    useToastStore.getState().addToast({
      type: "success",
      message: "자동 사라짐",
    });

    render(<ToastContainer />);
    expect(useToastStore.getState().toasts).toHaveLength(1);

    vi.advanceTimersByTime(5000);
    expect(useToastStore.getState().toasts).toHaveLength(0);

    vi.useRealTimers();
  });
});
