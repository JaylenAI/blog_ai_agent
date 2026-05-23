import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useArticles } from "../use-articles";
import { useArticleStore } from "../../stores/article-store";

vi.mock("../../api/client", () => ({
  api: {
    articles: {
      list: vi.fn(),
    },
  },
}));

import { api } from "../../api/client";
const mockList = vi.mocked(api.articles.list);

describe("useArticles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useArticleStore.getState().setArticles([]);
    useArticleStore.getState().setArticlesLoading(false);
  });

  it("fetches articles on mount and stores them", async () => {
    const articles = [
      {
        id: 1,
        slug: "a",
        topic: "test",
        title: "Test",
        status: "draft",
        category: "",
        format_id: "",
        content_path: "",
        word_count: 0,
        image_count: 0,
        created_at: "",
        updated_at: "",
      },
    ];
    mockList.mockResolvedValueOnce({
      success: true,
      data: { items: articles, total: 1, page: 1, limit: 20 },
    });

    renderHook(() => useArticles());

    await waitFor(() => {
      expect(useArticleStore.getState().articles).toHaveLength(1);
    });
    expect(mockList).toHaveBeenCalledOnce();
  });

  it("sets loading false even on failure", async () => {
    mockList.mockRejectedValueOnce(new Error("network"));

    renderHook(() => useArticles());

    await waitFor(() => {
      expect(
        useArticleStore.getState().articlesLoading,
      ).toBe(false);
    });
  });

  it("returns refetch function", async () => {
    mockList.mockResolvedValue({
      success: true,
      data: { items: [], total: 0, page: 1, limit: 20 },
    });

    const { result } = renderHook(() => useArticles());

    await waitFor(() => {
      expect(mockList).toHaveBeenCalledOnce();
    });

    expect(typeof result.current.refetch).toBe("function");
  });
});
