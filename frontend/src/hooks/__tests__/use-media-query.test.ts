import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIsMobile, useIsTablet } from "../use-media-query";

function mockMatchMedia(matches: boolean) {
  const listeners: Array<(e: MediaQueryListEvent) => void> = [];
  const mql = {
    matches,
    addEventListener: vi.fn((_: string, cb: (e: MediaQueryListEvent) => void) => {
      listeners.push(cb);
    }),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal("matchMedia", vi.fn(() => mql));
  return { mql, listeners };
}

describe("useIsMobile", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns true when window width < 768", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
  });

  it("returns false when window width >= 768", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it("responds to media query changes", () => {
    const { listeners } = mockMatchMedia(false);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);

    act(() => {
      listeners.forEach((cb) =>
        cb({ matches: true } as MediaQueryListEvent),
      );
    });
    expect(result.current).toBe(true);
  });

  it("accepts custom breakpoint", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useIsMobile(480));
    expect(result.current).toBe(true);
  });

  it("cleans up listener on unmount", () => {
    const { mql } = mockMatchMedia(false);
    const { unmount } = renderHook(() => useIsMobile());
    unmount();
    expect(mql.removeEventListener).toHaveBeenCalled();
  });
});

describe("useIsTablet", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns true when width < 1024", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useIsTablet());
    expect(result.current).toBe(true);
  });

  it("returns false when width >= 1024", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useIsTablet());
    expect(result.current).toBe(false);
  });
});
