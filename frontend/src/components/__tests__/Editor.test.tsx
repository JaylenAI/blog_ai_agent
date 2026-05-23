import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Editor } from "../editor/Editor";
import { useArticleStore } from "../../stores/article-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { useUIStore } from "../../stores/ui-store";
import type { Article } from "../../types/article";

vi.mock("../../api/client", () => ({
  api: {
    articles: {
      updateContent: vi.fn().mockResolvedValue({ success: true }),
      getContent: vi.fn().mockResolvedValue(null),
    },
  },
}));

vi.mock("../editor/LazyMarkdownRenderer", () => ({
  LazyMarkdownRenderer: ({ content }: { content: string }) => (
    <div data-testid="md-renderer">{content.slice(0, 100)}</div>
  ),
}));

import { api } from "../../api/client";

const baseArticle: Article = {
  id: 1,
  slug: "test-article",
  topic: "테스트 주제",
  title: "테스트 제목",
  status: "draft",
  category: "AI/LLM",
  format_id: "concept",
  content_path: "",
  word_count: 5000,
  image_count: 3,
  created_at: "2026-01-01",
  updated_at: "2026-01-01",
  tags: ["AI", "RAG", "LLM"],
  section_count: 7,
  reference_count: 10,
};

describe("Editor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useArticleStore.setState({
      pipelineMode: "idle",
      articleContent: null,
      activeArticle: null,
    });
    usePipelineStore.getState().reset();
    useUIStore.setState({ editorMode: "view", editDraft: null });
  });

  it("renders article title", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("테스트 제목")).toBeInTheDocument();
  });

  it("renders topic as subtitle when different from title", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("테스트 주제")).toBeInTheDocument();
  });

  it("renders category badge", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("AI/LLM")).toBeInTheDocument();
  });

  it("renders tags", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("#AI")).toBeInTheDocument();
    expect(screen.getByText("#RAG")).toBeInTheDocument();
    expect(screen.getByText("#LLM")).toBeInTheDocument();
  });

  it("renders word count", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText(/5,000자/)).toBeInTheDocument();
  });

  it("renders image count", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText(/이미지 3장/)).toBeInTheDocument();
  });

  it("shows pipeline mode label when active", () => {
    useArticleStore.setState({ pipelineMode: "research" });
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("Stage 2 · 자료수집")).toBeInTheDocument();
  });

  it("renders markdown content when available", () => {
    useArticleStore.setState({ articleContent: "# 테스트 콘텐츠" });
    render(<Editor article={baseArticle} />);
    expect(screen.getByTestId("md-renderer")).toBeInTheDocument();
  });

  it("shows skeleton sections in early stage without content", () => {
    useArticleStore.setState({ pipelineMode: "research" });
    render(<Editor article={baseArticle} />);
    expect(screen.getAllByText("대기").length).toBeGreaterThan(0);
  });

  it("shows edit button when content exists", () => {
    useArticleStore.setState({ articleContent: "# Content" });
    render(<Editor article={baseArticle} />);
    expect(screen.getByLabelText("편집")).toBeInTheDocument();
  });

  it("switches to edit mode on edit button click", () => {
    useArticleStore.setState({ articleContent: "# Content" });
    render(<Editor article={baseArticle} />);
    fireEvent.click(screen.getByLabelText("편집"));
    expect(useUIStore.getState().editorMode).toBe("edit");
  });

  it("shows cancel and save buttons in edit mode", () => {
    useArticleStore.setState({ articleContent: "# Content" });
    useUIStore.setState({ editorMode: "edit", editDraft: "# Content" });
    render(<Editor article={baseArticle} />);
    expect(screen.getByLabelText("편집 취소")).toBeInTheDocument();
    expect(screen.getByLabelText("저장")).toBeInTheDocument();
  });

  it("cancels editing and returns to view mode", () => {
    useArticleStore.setState({ articleContent: "# Content" });
    useUIStore.setState({ editorMode: "edit", editDraft: "# Content" });
    render(<Editor article={baseArticle} />);
    fireEvent.click(screen.getByLabelText("편집 취소"));
    expect(useUIStore.getState().editorMode).toBe("view");
  });

  it("saves content via API", async () => {
    useArticleStore.setState({ articleContent: "# Old" });
    useUIStore.setState({ editorMode: "edit", editDraft: "# Updated" });
    render(<Editor article={baseArticle} />);

    fireEvent.click(screen.getByLabelText("저장"));

    await waitFor(() => {
      expect(api.articles.updateContent).toHaveBeenCalledWith(1, "# Updated");
    });
  });

  it("uses topic as title when title is null", () => {
    const noTitleArticle = { ...baseArticle, title: null };
    render(<Editor article={noTitleArticle} />);
    expect(screen.getByText("테스트 주제")).toBeInTheDocument();
  });

  it("renders meta grid for articles with word count", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("참고자료")).toBeInTheDocument();
    expect(screen.getByText("대섹션")).toBeInTheDocument();
  });

  it("shows reference count in meta grid", () => {
    render(<Editor article={baseArticle} />);
    expect(screen.getByText("10")).toBeInTheDocument();
  });
});
