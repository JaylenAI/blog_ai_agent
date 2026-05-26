import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DashboardPanel } from "../panels/DashboardPanel";
import { useArticleStore } from "../../stores/article-store";
import { useUIStore } from "../../stores/ui-store";
import type { Article } from "../../types/article";

vi.mock("../../api/client", () => ({
  api: {
    articles: {
      update: vi.fn().mockResolvedValue({ success: true }),
    },
  },
}));

function makeArticle(overrides: Partial<Article> = {}): Article {
  return {
    id: 1,
    slug: "test",
    title: "Test",
    topic: "test-topic",
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

describe("DashboardPanel", () => {
  beforeEach(() => {
    useArticleStore.setState({
      articles: [],
      activeArticle: null,
    });
    useUIStore.setState({
      sidebarPanel: "dashboard",
    });
  });

  it("renders zero statistics when no articles", () => {
    const { container } = render(<DashboardPanel />);
    const labels = container.querySelectorAll(".dash-stat-label");
    const labelTexts = Array.from(labels).map((el) => el.textContent);
    expect(labelTexts).toContain("전체");
    expect(labelTexts).toContain("발행");
    expect(labelTexts).toContain("초안");
    expect(labelTexts).toContain("총 글자수");
  });

  it("renders correct article counts", () => {
    useArticleStore.setState({
      articles: [
        makeArticle({ id: 1, status: "draft", word_count: 1000 }),
        makeArticle({ id: 2, status: "published", word_count: 3000 }),
        makeArticle({ id: 3, status: "draft", word_count: 500 }),
        makeArticle({ id: 4, status: "published", word_count: 2000 }),
      ],
    });

    const { container } = render(<DashboardPanel />);
    const statValues = container.querySelectorAll(".dash-stat-value");
    const values = Array.from(statValues).map((el) => el.textContent);

    // total=4, published=2, draft=2, totalWords=6,500
    expect(values[0]).toBe("4");
    expect(values[1]).toBe("2");
    expect(values[2]).toBe("2");
    expect(values[3]).toBe("6,500");
  });

  it("renders total word count formatted with locale", () => {
    useArticleStore.setState({
      articles: [
        makeArticle({ id: 1, word_count: 5000 }),
        makeArticle({ id: 2, word_count: 3500 }),
      ],
    });

    render(<DashboardPanel />);
    expect(screen.getByText("8,500")).toBeInTheDocument();
  });

  it("renders search input", () => {
    render(<DashboardPanel />);
    expect(screen.getByPlaceholderText("검색...")).toBeInTheDocument();
  });

  it("renders filter and sort dropdowns", () => {
    render(<DashboardPanel />);
    expect(screen.getByText("전체 상태")).toBeInTheDocument();
    expect(screen.getByText("최신순")).toBeInTheDocument();
  });

  it("renders article list with titles", () => {
    useArticleStore.setState({
      articles: [
        makeArticle({ id: 1, title: "React 최적화", topic: "react" }),
        makeArticle({ id: 2, title: null, topic: "Python 기초" }),
      ],
    });

    render(<DashboardPanel />);
    expect(screen.getByText("React 최적화")).toBeInTheDocument();
    expect(screen.getByText("Python 기초")).toBeInTheDocument();
  });

  it("shows empty message when filters match nothing", () => {
    useArticleStore.setState({
      articles: [makeArticle({ id: 1, status: "draft", topic: "test" })],
    });

    render(<DashboardPanel />);
    const searchInput = screen.getByPlaceholderText("검색...");
    fireEvent.change(searchInput, { target: { value: "nonexistent-query-xyz" } });
    expect(screen.getByText("조건에 맞는 아티클이 없습니다.")).toBeInTheDocument();
  });

  it("filters articles by search text", () => {
    useArticleStore.setState({
      articles: [
        makeArticle({ id: 1, title: "React 가이드", topic: "react" }),
        makeArticle({ id: 2, title: "Python 입문", topic: "python" }),
      ],
    });

    render(<DashboardPanel />);
    const searchInput = screen.getByPlaceholderText("검색...");
    fireEvent.change(searchInput, { target: { value: "React" } });
    expect(screen.getByText("React 가이드")).toBeInTheDocument();
    expect(screen.queryByText("Python 입문")).not.toBeInTheDocument();
  });
});
