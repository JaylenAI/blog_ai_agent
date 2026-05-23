import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { HistoryTab } from "../tabs/HistoryTab";
import { useArticleStore } from "../../stores/article-store";
import type { Article } from "../../types/article";

const mockArticle: Article = {
  id: 1,
  slug: "test",
  title: "Test",
  topic: "test",
  category: null,
  format_id: "standard",
  status: "draft",
  content_path: null,
  word_count: 0,
  image_count: 0,
  created_at: "2026-01-01T00:00:00",
  updated_at: "2026-01-01T00:00:00",
};

const mockVersions = [
  { version_id: "v1", timestamp: "2026-01-01 10:00", size: 2048, word_count: 500 },
  { version_id: "v2", timestamp: "2026-01-02 14:30", size: 4096, word_count: 1200 },
];

const mockListVersions = vi.fn();
const mockGetVersionContent = vi.fn();
const mockRestoreVersion = vi.fn();
const mockGetContent = vi.fn();

vi.mock("../../api/client", () => ({
  api: {
    articles: {
      listVersions: (...args: unknown[]) => mockListVersions(...args),
      getVersionContent: (...args: unknown[]) => mockGetVersionContent(...args),
      restoreVersion: (...args: unknown[]) => mockRestoreVersion(...args),
      getContent: (...args: unknown[]) => mockGetContent(...args),
    },
  },
}));

describe("HistoryTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useArticleStore.setState({
      activeArticle: null,
      articleContent: null,
    });
    mockListVersions.mockResolvedValue({ success: true, data: [] });
  });

  it("renders empty state when no active article", () => {
    render(<HistoryTab />);
    expect(screen.getByText("아티클을 선택해 주세요")).toBeInTheDocument();
  });

  it("renders loading state while fetching versions", () => {
    mockListVersions.mockReturnValue(new Promise(() => {}));
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    expect(screen.getByText("버전 이력 불러오는 중...")).toBeInTheDocument();
  });

  it("renders empty state when no versions exist", async () => {
    mockListVersions.mockResolvedValue({ success: true, data: [] });
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      expect(screen.getByText(/저장된 버전이 없습니다/)).toBeInTheDocument();
    });
  });

  it("renders version list with metadata", async () => {
    mockListVersions.mockResolvedValue({ success: true, data: mockVersions });
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      expect(screen.getByText("2026-01-01 10:00")).toBeInTheDocument();
      expect(screen.getByText("2026-01-02 14:30")).toBeInTheDocument();
    });
    expect(screen.getByText(/500자/)).toBeInTheDocument();
    expect(screen.getByText(/1,200자/)).toBeInTheDocument();
  });

  it("renders total version count", async () => {
    mockListVersions.mockResolvedValue({ success: true, data: mockVersions });
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      expect(screen.getByText("2개")).toBeInTheDocument();
    });
  });

  it("renders restore buttons for each version", async () => {
    mockListVersions.mockResolvedValue({ success: true, data: mockVersions });
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      const restoreButtons = screen.getAllByText("복원");
      expect(restoreButtons).toHaveLength(2);
    });
  });

  it("calls restoreVersion API when restore button clicked", async () => {
    mockListVersions.mockResolvedValue({ success: true, data: mockVersions });
    mockRestoreVersion.mockResolvedValue({ success: true, data: { restored: true, word_count: 500 } });
    mockGetContent.mockResolvedValue("restored content");
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      expect(screen.getAllByText("복원")).toHaveLength(2);
    });

    fireEvent.click(screen.getAllByText("복원")[0]);
    await waitFor(() => {
      expect(mockRestoreVersion).toHaveBeenCalledWith(1, "v1");
    });
  });

  it("renders error state when fetch fails", async () => {
    mockListVersions.mockRejectedValue(new Error("Network error"));
    useArticleStore.setState({ activeArticle: mockArticle });

    render(<HistoryTab />);
    await waitFor(() => {
      expect(screen.getByText("버전 이력을 불러올 수 없습니다.")).toBeInTheDocument();
    });
  });
});
