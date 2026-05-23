import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Sidebar } from "../layout/Sidebar";
import { useArticleStore } from "../../stores/article-store";
import { useUIStore } from "../../stores/ui-store";
import { useNotificationStore } from "../../stores/notification-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import type { Article } from "../../types/article";

vi.mock("../../api/client", () => ({
  api: {
    articles: {
      delete: vi.fn().mockResolvedValue({ success: true }),
    },
  },
}));

vi.mock("../common/ConfirmModal", () => ({
  ConfirmModal: ({
    title,
    onConfirm,
    onCancel,
  }: {
    title: string;
    onConfirm: () => void;
    onCancel: () => void;
  }) => (
    <div data-testid="confirm-modal">
      <span>{title}</span>
      <button onClick={onConfirm}>confirm</button>
      <button onClick={onCancel}>cancel</button>
    </div>
  ),
}));

vi.mock("../common/Icons", () => ({
  Icons: {
    Search: () => <span data-testid="icon-search" />,
    Plus: () => <span data-testid="icon-plus" />,
    Inbox: () => <span data-testid="icon-inbox" />,
    Folder: () => <span data-testid="icon-folder" />,
    Doc: () => <span data-testid="icon-doc" />,
    Send: () => <span data-testid="icon-send" />,
    Tag: () => <span data-testid="icon-tag" />,
    Layers: () => <span data-testid="icon-layers" />,
    Bot: () => <span data-testid="icon-bot" />,
    Sparkle: () => <span data-testid="icon-sparkle" />,
    Beaker: () => <span data-testid="icon-beaker" />,
    Hash: () => <span data-testid="icon-hash" />,
    Globe: () => <span data-testid="icon-globe" />,
    Cog: () => <span data-testid="icon-cog" />,
    X: ({ s: _s, w: _w }: { s?: number; w?: number }) => (
      <span data-testid="icon-x" />
    ),
    Chevron: ({
      s: _s,
      w: _w,
      className: _cls,
    }: {
      s?: number;
      w?: number;
      className?: string;
    }) => <span data-testid="icon-chevron" />,
  },
}));

function makeArticle(overrides: Partial<Article> = {}): Article {
  return {
    id: 1,
    slug: "test-slug",
    title: "테스트 글",
    topic: "테스트 주제",
    category: null,
    format_id: "standard",
    status: "draft",
    content_path: null,
    word_count: 0,
    image_count: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("Sidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useArticleStore.setState({
      articles: [],
      activeArticle: null,
      pipelineMode: "idle",
      articleContent: null,
      gateModal: null,
      articlesLoading: false,
    });
    useUIStore.setState({
      sidebarPanel: null,
      rightPanelOpen: true,
      rightPanelTab: "pipeline",
    });
    useNotificationStore.setState({
      notifications: [],
    });
    usePipelineStore.setState({
      events: [],
      currentRun: null,
      isRunning: false,
      error: null,
    });
  });

  it("브랜드 마크와 앱 이름을 렌더링한다", () => {
    render(<Sidebar />);
    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.getByText("Blog Agent")).toBeInTheDocument();
    expect(screen.getByText("v0.4")).toBeInTheDocument();
  });

  it("아티클 목록을 렌더링한다", () => {
    const articles = [
      makeArticle({ id: 1, title: "첫 번째 글", status: "draft" }),
      makeArticle({ id: 2, title: "두 번째 글", status: "draft" }),
    ];
    useArticleStore.setState({ articles });

    render(<Sidebar />);
    expect(screen.getByText("첫 번째 글")).toBeInTheDocument();
    expect(screen.getByText("두 번째 글")).toBeInTheDocument();
  });

  it("아티클이 없을 때 Drafts 카운트가 0이다", () => {
    useArticleStore.setState({ articles: [] });

    render(<Sidebar />);
    const draftCount = screen.getByText("Drafts")
      .closest(".sb-row")
      ?.querySelector(".count");
    expect(draftCount?.textContent).toBe("0");
  });

  it("검색 필터링이 동작한다", () => {
    const articles = [
      makeArticle({ id: 1, title: "React 튜토리얼", topic: "react" }),
      makeArticle({ id: 2, title: "Python 가이드", topic: "python" }),
      makeArticle({ id: 3, title: null, topic: "react hooks" }),
    ];
    useArticleStore.setState({ articles });

    render(<Sidebar />);

    fireEvent.click(screen.getByText("검색"));

    const searchInput = screen.getByPlaceholderText("제목 또는 주제 검색...");
    fireEvent.change(searchInput, { target: { value: "react" } });

    expect(screen.getByText("React 튜토리얼")).toBeInTheDocument();
    expect(screen.getByText("react hooks")).toBeInTheDocument();
    expect(screen.queryByText("Python 가이드")).not.toBeInTheDocument();
  });

  it("아티클 클릭 시 setActiveArticle이 호출된다", () => {
    const article = makeArticle({ id: 10, title: "클릭 테스트" });
    useArticleStore.setState({ articles: [article] });

    render(<Sidebar />);

    fireEvent.click(screen.getByText("클릭 테스트"));

    const state = useArticleStore.getState();
    expect(state.activeArticle?.id).toBe(10);
  });

  it("unread 알림이 있을 때 배지를 표시한다", () => {
    useNotificationStore.setState({
      notifications: [
        {
          id: "n1",
          type: "info",
          title: "테스트 알림",
          message: "테스트",
          timestamp: Date.now(),
          read: false,
        },
        {
          id: "n2",
          type: "complete",
          title: "완료",
          message: "완료됨",
          timestamp: Date.now(),
          read: false,
        },
      ],
    });

    render(<Sidebar />);

    const alarmRow = screen.getByText("알림").closest(".sb-row");
    const badge = alarmRow?.querySelector(".count");
    expect(badge?.textContent).toBe("2");
  });

  it("published 아티클은 Published 섹션에 표시된다", () => {
    const articles = [
      makeArticle({ id: 1, title: "초안 글", status: "draft" }),
      makeArticle({ id: 2, title: "발행된 글", status: "published" }),
    ];
    useArticleStore.setState({ articles });

    render(<Sidebar />);

    // Published 섹션을 열기
    fireEvent.click(screen.getByText("Published"));

    expect(screen.getByText("발행된 글")).toBeInTheDocument();
  });

  it("'새 글 만들기' 클릭 시 activeArticle이 null로 설정된다", () => {
    const article = makeArticle({ id: 1, title: "기존 글" });
    useArticleStore.setState({ articles: [article], activeArticle: article });

    render(<Sidebar />);

    fireEvent.click(screen.getByText("새 글 만들기"));

    const state = useArticleStore.getState();
    expect(state.activeArticle).toBeNull();
  });
});
