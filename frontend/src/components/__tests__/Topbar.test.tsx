import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Topbar } from "../layout/Topbar";
import { useArticleStore } from "../../stores/article-store";
import { useUIStore } from "../../stores/ui-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import type { Article } from "../../types/article";

vi.mock("../../api/client", () => ({
  api: {
    pipeline: {
      cancel: vi.fn().mockResolvedValue(undefined),
    },
    articles: {
      getContent: vi.fn().mockResolvedValue("content"),
      saveObsidian: vi.fn().mockResolvedValue({ success: true }),
    },
  },
}));

vi.mock("../../hooks/use-pipeline-sse", () => ({
  usePipelineSSE: () => ({
    startStream: vi.fn().mockResolvedValue(undefined),
  }),
}));

vi.mock("../common/Icons", () => ({
  Icons: {
    Menu: () => <span data-testid="icon-menu" />,
    Sidebar: () => <span data-testid="icon-sidebar" />,
    Moon: ({ s: _s }: { s?: number }) => <span data-testid="icon-moon" />,
    Sun: ({ s: _s }: { s?: number }) => <span data-testid="icon-sun" />,
    Send: ({ s: _s }: { s?: number }) => <span data-testid="icon-send" />,
    Layers: ({ s: _s }: { s?: number }) => (
      <span data-testid="icon-layers" />
    ),
    X: ({ s: _s }: { s?: number }) => <span data-testid="icon-x" />,
    Sparkle: ({ s: _s }: { s?: number }) => (
      <span data-testid="icon-sparkle" />
    ),
    CheckCircle: ({ s: _s }: { s?: number }) => (
      <span data-testid="icon-check" />
    ),
    Doc: ({ s: _s }: { s?: number }) => <span data-testid="icon-doc" />,
  },
}));

function makeArticle(overrides: Partial<Article> = {}): Article {
  return {
    id: 1,
    slug: "test",
    title: "테스트 글",
    topic: "테스트",
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
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("Topbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useArticleStore.setState({
      articles: [],
      activeArticle: null,
      pipelineMode: "idle",
      articleContent: null,
      gateModal: null,
    });
    useUIStore.setState({
      theme: "light",
      sidebarOpen: true,
      rightPanelOpen: true,
      publishKitOpen: false,
    });
    usePipelineStore.setState({
      currentRun: null,
      events: [],
      isRunning: false,
      error: null,
    });
  });

  it("breadcrumb에 '새 글'을 표시한다 (activeArticle이 없을 때)", () => {
    render(<Topbar />);
    expect(screen.getByText("새 글")).toBeInTheDocument();
    expect(screen.getByText("AI의 정석")).toBeInTheDocument();
    expect(screen.getByText("Drafts")).toBeInTheDocument();
  });

  it("activeArticle이 있을 때 제목을 breadcrumb에 표시한다", () => {
    const article = makeArticle({ title: "React 심층분석" });
    useArticleStore.setState({ activeArticle: article, articles: [article] });

    render(<Topbar />);
    expect(screen.getByText("React 심층분석")).toBeInTheDocument();
  });

  it("사이드바 토글 버튼이 동작한다", () => {
    render(<Topbar />);

    const sidebarBtn = screen.getByLabelText("사이드바 토글");
    const beforeState = useUIStore.getState().sidebarOpen;
    fireEvent.click(sidebarBtn);
    expect(useUIStore.getState().sidebarOpen).toBe(!beforeState);
  });

  it("테마 토글이 동작한다 (light -> dark)", () => {
    useUIStore.setState({ theme: "light" });

    render(<Topbar />);

    const themeBtn = screen.getByLabelText("테마 전환");
    expect(screen.getByTestId("icon-moon")).toBeInTheDocument();

    fireEvent.click(themeBtn);
    expect(useUIStore.getState().theme).toBe("dark");
  });

  it("다크 모드일 때 Sun 아이콘을 표시한다", () => {
    useUIStore.setState({ theme: "dark" });

    render(<Topbar />);
    expect(screen.getByTestId("icon-sun")).toBeInTheDocument();
  });

  it("hamburger 모드일 때 메뉴 버튼을 표시한다", () => {
    const handleHamburger = vi.fn();

    render(<Topbar hamburger onHamburgerClick={handleHamburger} />);

    const menuBtn = screen.getByLabelText("메뉴 열기");
    fireEvent.click(menuBtn);
    expect(handleHamburger).toHaveBeenCalledOnce();
  });

  it("파이프라인 패널 토글 버튼이 동작한다", () => {
    render(<Topbar />);

    const panelBtn = screen.getByLabelText("파이프라인 패널");
    const beforeState = useUIStore.getState().rightPanelOpen;
    fireEvent.click(panelBtn);
    expect(useUIStore.getState().rightPanelOpen).toBe(!beforeState);
  });

  it("파이프라인 모드가 research일 때 상태 pill을 표시한다", () => {
    useArticleStore.setState({ pipelineMode: "research" });

    render(<Topbar />);
    expect(
      screen.getByText("Researcher · 자료수집 중"),
    ).toBeInTheDocument();
  });

  it("파이프라인 idle일 때 pill을 표시하지 않는다", () => {
    useArticleStore.setState({ pipelineMode: "idle" });

    render(<Topbar />);
    expect(
      screen.queryByText("Researcher · 자료수집 중"),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("준비")).not.toBeInTheDocument();
  });
});
