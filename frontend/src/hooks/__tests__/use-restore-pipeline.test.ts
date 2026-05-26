import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useRestorePipeline } from "../use-restore-pipeline";
import { useArticleStore } from "../../stores/article-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import type { PipelineRun } from "../../types/pipeline";
import type { Article } from "../../types/article";

vi.mock("../../api/client", () => ({
  api: {
    pipeline: {
      getActiveRun: vi.fn(),
    },
    articles: {
      get: vi.fn(),
      getContent: vi.fn(),
    },
  },
}));

import { api } from "../../api/client";
const mockGetActiveRun = vi.mocked(api.pipeline.getActiveRun);
const mockGetArticle = vi.mocked(api.articles.get);
const mockGetContent = vi.mocked(api.articles.getContent);

function makeRun(overrides: Partial<PipelineRun> & { id: number; article_id: number }): PipelineRun {
  return {
    current_stage: "router",
    status: "running",
    started_at: "2026-01-01T00:00:00",
    completed_at: null,
    ...overrides,
  };
}

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
    tags: [],
    reference_count: 0,
    section_count: 0,
    thumbnail_path: "",
    created_at: "2026-01-01T00:00:00",
    updated_at: "2026-01-01T00:00:00",
    ...overrides,
  };
}

describe("useRestorePipeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePipelineStore.getState().reset();
    useArticleStore.getState().setPipelineMode("idle");
    useArticleStore.getState().closeGateModal();
  });

  it("does nothing when no active run", async () => {
    mockGetActiveRun.mockResolvedValueOnce({
      success: true,
      data: null,
    });

    renderHook(() => useRestorePipeline());

    await waitFor(() => {
      expect(mockGetActiveRun).toHaveBeenCalledOnce();
    });
    expect(mockGetArticle).not.toHaveBeenCalled();
  });

  it("restores running pipeline state", async () => {
    mockGetActiveRun.mockResolvedValueOnce({
      success: true,
      data: makeRun({ id: 5, article_id: 3, current_stage: "researcher", status: "running" }),
    });
    mockGetArticle.mockResolvedValueOnce({
      success: true,
      data: makeArticle({ id: 3, slug: "test", topic: "test", title: "Test", status: "draft" }),
    });

    renderHook(() => useRestorePipeline());

    await waitFor(() => {
      expect(usePipelineStore.getState().isRunning).toBe(true);
    });
  });

  it("opens gate modal for paused gate_one run", async () => {
    mockGetActiveRun.mockResolvedValueOnce({
      success: true,
      data: makeRun({ id: 10, article_id: 2, current_stage: "gate_one", status: "paused" }),
    });
    mockGetArticle.mockResolvedValueOnce({
      success: true,
      data: makeArticle({ id: 2, slug: "s", topic: "t", title: "T", status: "draft" }),
    });

    renderHook(() => useRestorePipeline());

    await waitFor(() => {
      expect(useArticleStore.getState().gateModal).toEqual({
        gate: "gate_one",
        runId: 10,
      });
    });
  });

  it("fetches content for paused gate_two", async () => {
    mockGetActiveRun.mockResolvedValueOnce({
      success: true,
      data: makeRun({ id: 11, article_id: 4, current_stage: "gate_two", status: "paused" }),
    });
    mockGetArticle.mockResolvedValueOnce({
      success: true,
      data: makeArticle({ id: 4, slug: "s", topic: "t", title: "T", status: "draft" }),
    });
    mockGetContent.mockResolvedValueOnce("# Content");

    renderHook(() => useRestorePipeline());

    await waitFor(() => {
      expect(mockGetContent).toHaveBeenCalledWith(4);
    });
  });

  it("handles restore failure gracefully", async () => {
    mockGetActiveRun.mockRejectedValueOnce(new Error("network"));

    renderHook(() => useRestorePipeline());

    await waitFor(() => {
      expect(mockGetActiveRun).toHaveBeenCalledOnce();
    });
  });
});
