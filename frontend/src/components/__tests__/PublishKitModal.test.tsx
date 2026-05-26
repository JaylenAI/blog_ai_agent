import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { PublishKitModal } from "../publish/PublishKitModal";

const mockGet = vi.fn();
const mockGetHtml = vi.fn();

vi.mock("../../api/client", () => ({
  api: {
    publishKit: { get: (...args: unknown[]) => mockGet(...args) },
    articles: { getHtml: (...args: unknown[]) => mockGetHtml(...args) },
  },
}));

vi.mock("../editor/LazyMarkdownRenderer", () => ({
  LazyMarkdownRenderer: ({ content }: { content: string }) => (
    <div data-testid="md-renderer">{content.slice(0, 50)}</div>
  ),
}));

const mockOnClose = vi.fn();

const mockKit = {
  title: "테스트 글",
  category: "AI/ML",
  tags: ["LLM", "GPT", "AI"],
  markdown: "# 테스트\n\n본문입니다.",
  html: "<h1>테스트</h1><p>본문입니다.</p>",
  images: [{ name: "image1.png", url: "/api/v1/articles/1/images/image1.png" }],
  diagrams: [{ name: "flow.mmd", content: "graph TD\n  A-->B" }],
  references: [
    {
      url: "https://example.com/ref1",
      title: "참고자료 1",
      summary: "첫 번째 참고자료 요약",
      relevance_score: 0.95,
      source_type: "official",
    },
    {
      url: "https://github.com/repo",
      title: "GitHub 자료",
      summary: "GitHub 참고자료",
      relevance_score: 0.85,
      source_type: "github",
    },
  ],
  thumbnail_url: "/api/v1/articles/1/images/thumbnail.png",
  word_count: 1500,
  status: "published",
};

describe("PublishKitModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue({ success: true, data: mockKit });
    mockGetHtml.mockResolvedValue(null);
  });

  it("renders header with title and word count", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => {
      expect(screen.getByText(/테스트 글/)).toBeInTheDocument();
      expect(screen.getByText(/1,500자/)).toBeInTheDocument();
    });
  });

  it("renders all 5 tabs", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => {
      expect(screen.getByText("Markdown")).toBeInTheDocument();
      expect(screen.getByText("HTML")).toBeInTheDocument();
      expect(screen.getByText("메타 정보")).toBeInTheDocument();
      expect(screen.getByText("참고자료")).toBeInTheDocument();
      expect(screen.getByText("이미지")).toBeInTheDocument();
    });
  });

  it("shows references badge with count", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => {
      const badges = screen.getAllByText("2");
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows markdown tab by default", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => {
      expect(screen.getByText("렌더링")).toBeInTheDocument();
      expect(screen.getByText("원본")).toBeInTheDocument();
    });
  });

  it("switches to meta tab and shows metadata", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("메타 정보"));
    fireEvent.click(screen.getByText("메타 정보"));
    expect(screen.getByText("AI/ML")).toBeInTheDocument();
    expect(screen.getByText("LLM, GPT, AI")).toBeInTheDocument();
  });

  it("switches to references tab and shows references", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("참고자료"));
    fireEvent.click(screen.getByText("참고자료"));
    await waitFor(() => {
      expect(screen.getByText("참고자료 1")).toBeInTheDocument();
      expect(screen.getByText("GitHub 자료")).toBeInTheDocument();
      expect(screen.getByText("95%")).toBeInTheDocument();
      expect(screen.getByText("85%")).toBeInTheDocument();
    });
  });

  it("groups references by source type", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("참고자료"));
    fireEvent.click(screen.getByText("참고자료"));
    await waitFor(() => {
      expect(screen.getByText("공식")).toBeInTheDocument();
      expect(screen.getByText("GitHub")).toBeInTheDocument();
    });
  });

  it("switches to images tab and shows thumbnail", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("이미지"));
    fireEvent.click(screen.getByText("이미지"));
    await waitFor(() => {
      expect(screen.getByText("썸네일")).toBeInTheDocument();
      expect(screen.getByAltText("썸네일")).toBeInTheDocument();
    });
  });

  it("shows image cards in images tab", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("이미지"));
    fireEvent.click(screen.getByText("이미지"));
    await waitFor(() => {
      expect(screen.getByText("image1.png")).toBeInTheDocument();
    });
  });

  it("shows diagram code in images tab", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("이미지"));
    fireEvent.click(screen.getByText("이미지"));
    await waitFor(() => {
      expect(screen.getByText("flow.mmd")).toBeInTheDocument();
    });
  });

  it("calls onClose on Escape key", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    fireEvent.keyDown(window, { key: "Escape" });
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("calls onClose when clicking overlay", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    const overlay = document.querySelector(".pk-overlay")!;
    fireEvent.click(overlay);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it("does not call onClose when clicking modal body", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    const modal = document.querySelector(".pk-modal")!;
    fireEvent.click(modal);
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it("has proper ARIA attributes", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("aria-modal", "true");
    expect(dialog).toHaveAttribute("aria-labelledby", "pk-modal-title");
  });

  it("shows loading state initially", () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    expect(screen.getByText("불러오는 중...")).toBeInTheDocument();
  });

  it("shows published status in meta tab", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("메타 정보"));
    fireEvent.click(screen.getByText("메타 정보"));
    expect(screen.getByText("발행 완료")).toBeInTheDocument();
  });

  it("shows tag chips in meta tab", async () => {
    render(<PublishKitModal articleId={1} onClose={mockOnClose} />);
    await waitFor(() => screen.getByText("메타 정보"));
    fireEvent.click(screen.getByText("메타 정보"));
    expect(screen.getByText("LLM")).toBeInTheDocument();
    expect(screen.getByText("GPT")).toBeInTheDocument();
    expect(screen.getByText("AI")).toBeInTheDocument();
  });
});
