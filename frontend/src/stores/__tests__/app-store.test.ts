import { describe, it, expect, beforeEach } from "vitest";
import { useUIStore } from "../ui-store";
import { useArticleStore } from "../article-store";
import { useToastStore } from "../toast-store";
import type { Article } from "../../types/article";

function makeArticle(overrides: Partial<Article> & { id: number }): Article {
  return {
    slug: "test",
    title: null,
    topic: "test",
    category: null,
    format_id: "standard",
    status: "draft",
    content_path: null,
    word_count: 0,
    image_count: 0,
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
    ...overrides,
  };
}

describe("useUIStore", () => {
  beforeEach(() => {
    useUIStore.setState({
      sidebarOpen: true,
      rightPanelOpen: true,
      rightPanelTab: "pipeline",
      sidebarPanel: null,
      publishKitOpen: false,
      editorMode: "view",
      editDraft: null,
    });
  });

  it("toggleSidebar flips sidebarOpen", () => {
    expect(useUIStore.getState().sidebarOpen).toBe(true);
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(false);
    useUIStore.getState().toggleSidebar();
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it("toggleRightPanel flips rightPanelOpen", () => {
    expect(useUIStore.getState().rightPanelOpen).toBe(true);
    useUIStore.getState().toggleRightPanel();
    expect(useUIStore.getState().rightPanelOpen).toBe(false);
  });

  it("setRightPanelTab changes tab", () => {
    useUIStore.getState().setRightPanelTab("references");
    expect(useUIStore.getState().rightPanelTab).toBe("references");
  });

  it("setTheme and setDensity update display settings", () => {
    useUIStore.getState().setTheme("dark");
    expect(useUIStore.getState().theme).toBe("dark");
    useUIStore.getState().setDensity("compact");
    expect(useUIStore.getState().density).toBe("compact");
  });

  it("setSidebarPanel toggles panel", () => {
    useUIStore.getState().setSidebarPanel("pipelines");
    expect(useUIStore.getState().sidebarPanel).toBe("pipelines");
    useUIStore.getState().setSidebarPanel("pipelines");
    expect(useUIStore.getState().sidebarPanel).toBeNull();
  });

  it("setSidebarPanel switches to different panel", () => {
    useUIStore.getState().setSidebarPanel("pipelines");
    useUIStore.getState().setSidebarPanel("style-guide");
    expect(useUIStore.getState().sidebarPanel).toBe("style-guide");
  });

  it("setPublishKitOpen toggles publish kit modal", () => {
    expect(useUIStore.getState().publishKitOpen).toBe(false);
    useUIStore.getState().setPublishKitOpen(true);
    expect(useUIStore.getState().publishKitOpen).toBe(true);
    useUIStore.getState().setPublishKitOpen(false);
    expect(useUIStore.getState().publishKitOpen).toBe(false);
  });

  it("setEditorMode switches modes and clears draft on view", () => {
    useUIStore.getState().setEditDraft("# hello");
    useUIStore.getState().setEditorMode("edit");
    expect(useUIStore.getState().editorMode).toBe("edit");
    useUIStore.getState().setEditorMode("view");
    expect(useUIStore.getState().editorMode).toBe("view");
    expect(useUIStore.getState().editDraft).toBeNull();
  });
});

describe("useArticleStore", () => {
  beforeEach(() => {
    useArticleStore.setState({
      activeArticle: null,
      pipelineMode: "idle",
      articles: [],
      articleContent: null,
      gateModal: null,
      articlesLoading: false,
    });
  });

  it("setActiveArticle clears articleContent", () => {
    useArticleStore.setState({ articleContent: "some content" });
    const article = makeArticle({ id: 1, slug: "test", topic: "test", status: "draft" });
    useArticleStore.getState().setActiveArticle(article);
    expect(useArticleStore.getState().activeArticle).toEqual(article);
    expect(useArticleStore.getState().articleContent).toBeNull();
  });

  it("addArticle prepends to articles array", () => {
    const a1 = makeArticle({ id: 1, slug: "a1", topic: "first" });
    const a2 = makeArticle({ id: 2, slug: "a2", topic: "second" });
    useArticleStore.getState().addArticle(a1);
    useArticleStore.getState().addArticle(a2);
    const articles = useArticleStore.getState().articles;
    expect(articles).toHaveLength(2);
    expect(articles[0]!.id).toBe(2);
  });

  it("openGateModal and closeGateModal work correctly", () => {
    useArticleStore.getState().openGateModal("gate_one", 42);
    expect(useArticleStore.getState().gateModal).toEqual({ gate: "gate_one", runId: 42 });
    useArticleStore.getState().closeGateModal();
    expect(useArticleStore.getState().gateModal).toBeNull();
  });

  it("setPipelineMode updates mode", () => {
    useArticleStore.getState().setPipelineMode("research");
    expect(useArticleStore.getState().pipelineMode).toBe("research");
  });
});

describe("useToastStore", () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it("addToast creates toast with unique id", () => {
    useToastStore.getState().addToast({ type: "error", message: "test error" });
    const toasts = useToastStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0]!.type).toBe("error");
    expect(toasts[0]!.id).toBeTruthy();
  });

  it("removeToast removes by id", () => {
    useToastStore.getState().addToast({ type: "success", message: "ok" });
    const id = useToastStore.getState().toasts[0]!.id;
    useToastStore.getState().removeToast(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });
});
