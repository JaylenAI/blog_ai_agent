import { describe, it, expect, beforeEach } from "vitest";
import { useArticleStore } from "../article-store";
import { act } from "@testing-library/react";
import type { Article } from "../../types/article";

const mockArticle: Article = {
  id: 1,
  slug: "test-article",
  title: "테스트 글",
  topic: "MCP 서버",
  category: "AI",
  format_id: "concept",
  status: "draft",
  content_path: null,
  word_count: 0,
  image_count: 0,
  created_at: "2026-01-01",
  updated_at: "2026-01-01",
};

beforeEach(() => {
  act(() =>
    useArticleStore.setState({
      activeArticle: null,
      pipelineMode: "idle",
      articles: [],
      articleContent: null,
      gateModal: null,
      articlesLoading: false,
    }),
  );
});

describe("useArticleStore", () => {
  it("initializes with default values", () => {
    const s = useArticleStore.getState();
    expect(s.activeArticle).toBeNull();
    expect(s.pipelineMode).toBe("idle");
    expect(s.articles).toEqual([]);
    expect(s.articleContent).toBeNull();
    expect(s.gateModal).toBeNull();
    expect(s.articlesLoading).toBe(false);
  });

  it("setActiveArticle sets article and clears content", () => {
    act(() => useArticleStore.getState().setArticleContent("old content"));
    act(() => useArticleStore.getState().setActiveArticle(mockArticle));
    const s = useArticleStore.getState();
    expect(s.activeArticle).toEqual(mockArticle);
    expect(s.articleContent).toBeNull();
  });

  it("setActiveArticle to null clears article", () => {
    act(() => useArticleStore.getState().setActiveArticle(mockArticle));
    act(() => useArticleStore.getState().setActiveArticle(null));
    expect(useArticleStore.getState().activeArticle).toBeNull();
  });

  it("setPipelineMode updates mode", () => {
    act(() => useArticleStore.getState().setPipelineMode("research"));
    expect(useArticleStore.getState().pipelineMode).toBe("research");
    act(() => useArticleStore.getState().setPipelineMode("generate"));
    expect(useArticleStore.getState().pipelineMode).toBe("generate");
  });

  it("setArticles replaces articles list", () => {
    const articles = [mockArticle, { ...mockArticle, id: 2, slug: "second" }];
    act(() => useArticleStore.getState().setArticles(articles));
    expect(useArticleStore.getState().articles).toHaveLength(2);
  });

  it("addArticle prepends to list", () => {
    const existing = { ...mockArticle, id: 1 };
    const newArticle = { ...mockArticle, id: 2, slug: "new" };
    act(() => useArticleStore.getState().setArticles([existing]));
    act(() => useArticleStore.getState().addArticle(newArticle));
    const articles = useArticleStore.getState().articles;
    expect(articles).toHaveLength(2);
    expect(articles[0].id).toBe(2);
  });

  it("setArticleContent updates content", () => {
    act(() => useArticleStore.getState().setArticleContent("# 새 내용"));
    expect(useArticleStore.getState().articleContent).toBe("# 새 내용");
  });

  it("openGateModal sets gate and runId", () => {
    act(() => useArticleStore.getState().openGateModal("gate_one", 42));
    const modal = useArticleStore.getState().gateModal;
    expect(modal).toEqual({ gate: "gate_one", runId: 42 });
  });

  it("closeGateModal clears modal", () => {
    act(() => useArticleStore.getState().openGateModal("gate_two", 10));
    act(() => useArticleStore.getState().closeGateModal());
    expect(useArticleStore.getState().gateModal).toBeNull();
  });

  it("setArticlesLoading updates flag", () => {
    act(() => useArticleStore.getState().setArticlesLoading(true));
    expect(useArticleStore.getState().articlesLoading).toBe(true);
    act(() => useArticleStore.getState().setArticlesLoading(false));
    expect(useArticleStore.getState().articlesLoading).toBe(false);
  });

  it("immutability - addArticle creates new array", () => {
    act(() => useArticleStore.getState().setArticles([mockArticle]));
    const before = useArticleStore.getState().articles;
    act(() =>
      useArticleStore.getState().addArticle({ ...mockArticle, id: 99 }),
    );
    const after = useArticleStore.getState().articles;
    expect(before).not.toBe(after);
  });
});
