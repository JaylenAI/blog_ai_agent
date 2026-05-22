import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore } from "../app-store";

describe("useAppStore", () => {
  beforeEach(() => {
    useAppStore.setState({
      sidebarOpen: true,
      rightPanelOpen: true,
      rightPanelTab: "pipeline",
      activeArticle: null,
      pipelineMode: "idle",
      articles: [],
      articleContent: null,
      gateModal: null,
      articlesLoading: false,
      toasts: [],
    });
  });

  it("toggleSidebar flips sidebarOpen", () => {
    expect(useAppStore.getState().sidebarOpen).toBe(true);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(false);
    useAppStore.getState().toggleSidebar();
    expect(useAppStore.getState().sidebarOpen).toBe(true);
  });

  it("toggleRightPanel flips rightPanelOpen", () => {
    expect(useAppStore.getState().rightPanelOpen).toBe(true);
    useAppStore.getState().toggleRightPanel();
    expect(useAppStore.getState().rightPanelOpen).toBe(false);
  });

  it("setRightPanelTab changes tab", () => {
    useAppStore.getState().setRightPanelTab("references");
    expect(useAppStore.getState().rightPanelTab).toBe("references");
  });

  it("setActiveArticle clears articleContent", () => {
    useAppStore.setState({ articleContent: "some content" });
    const article = { id: 1, slug: "test", topic: "test", status: "draft" } as any;
    useAppStore.getState().setActiveArticle(article);
    expect(useAppStore.getState().activeArticle).toEqual(article);
    expect(useAppStore.getState().articleContent).toBeNull();
  });

  it("addArticle prepends to articles array", () => {
    const a1 = { id: 1, slug: "a1", topic: "first" } as any;
    const a2 = { id: 2, slug: "a2", topic: "second" } as any;
    useAppStore.getState().addArticle(a1);
    useAppStore.getState().addArticle(a2);
    const articles = useAppStore.getState().articles;
    expect(articles).toHaveLength(2);
    expect(articles[0]!.id).toBe(2);
  });

  it("openGateModal and closeGateModal work correctly", () => {
    useAppStore.getState().openGateModal("gate_one", 42);
    expect(useAppStore.getState().gateModal).toEqual({ gate: "gate_one", runId: 42 });
    useAppStore.getState().closeGateModal();
    expect(useAppStore.getState().gateModal).toBeNull();
  });

  it("addToast creates toast with unique id", () => {
    useAppStore.getState().addToast({ type: "error", message: "test error" });
    const toasts = useAppStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0]!.type).toBe("error");
    expect(toasts[0]!.id).toBeTruthy();
  });

  it("removeToast removes by id", () => {
    useAppStore.getState().addToast({ type: "success", message: "ok" });
    const id = useAppStore.getState().toasts[0]!.id;
    useAppStore.getState().removeToast(id);
    expect(useAppStore.getState().toasts).toHaveLength(0);
  });

  it("setPipelineMode updates mode", () => {
    useAppStore.getState().setPipelineMode("research");
    expect(useAppStore.getState().pipelineMode).toBe("research");
  });

  it("setTheme and setDensity update display settings", () => {
    useAppStore.getState().setTheme("dark");
    expect(useAppStore.getState().theme).toBe("dark");
    useAppStore.getState().setDensity("compact");
    expect(useAppStore.getState().density).toBe("compact");
  });
});
