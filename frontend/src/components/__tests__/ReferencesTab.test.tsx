import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReferencesTab } from "../tabs/ReferencesTab";
import { usePipelineStore } from "../../stores/pipeline-store";
import type { PipelineEvent } from "../../types/pipeline";

interface Reference {
  url: string;
  title: string;
  summary: string;
  relevance_score: number;
  source_type: string;
}

function makeResearchCompleteEvent(references: Reference[]): PipelineEvent {
  return {
    event_type: "stage_complete",
    stage: "researcher",
    message: "Research complete",
    data: { references },
  };
}

const sampleReferences: Reference[] = [
  {
    url: "https://example.com/article-1",
    title: "React 성능 최적화 가이드",
    summary: "React 렌더링 최적화에 대한 상세 가이드",
    relevance_score: 0.95,
    source_type: "blog",
  },
  {
    url: "https://docs.python.org/3/tutorial",
    title: "Python 공식 튜토리얼",
    summary: "Python 공식 문서의 튜토리얼 섹션",
    relevance_score: 0.8,
    source_type: "official",
  },
  {
    url: "https://github.com/example/repo",
    title: "예제 리포지토리",
    summary: "관련 오픈소스 프로젝트",
    relevance_score: 0.6,
    source_type: "github",
  },
];

describe("ReferencesTab", () => {
  beforeEach(() => {
    usePipelineStore.setState({ events: [] });
  });

  it("renders empty state when no references", () => {
    render(<ReferencesTab />);
    expect(
      screen.getByText("파이프라인 실행 후 자료가 표시됩니다"),
    ).toBeInTheDocument();
  });

  it("renders empty state when research event has no references", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent([])],
    });

    render(<ReferencesTab />);
    expect(
      screen.getByText("파이프라인 실행 후 자료가 표시됩니다"),
    ).toBeInTheDocument();
  });

  it("renders reference list with titles", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent(sampleReferences)],
    });

    render(<ReferencesTab />);
    expect(screen.getByText("React 성능 최적화 가이드")).toBeInTheDocument();
    expect(screen.getByText("Python 공식 튜토리얼")).toBeInTheDocument();
    expect(screen.getByText("예제 리포지토리")).toBeInTheDocument();
  });

  it("renders total reference count", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent(sampleReferences)],
    });

    render(<ReferencesTab />);
    expect(screen.getByText("3건")).toBeInTheDocument();
  });

  it("renders reference links with correct href and target", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent(sampleReferences)],
    });

    render(<ReferencesTab />);
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(3);
    expect(links[0]).toHaveAttribute("href", "https://example.com/article-1");
    expect(links[0]).toHaveAttribute("target", "_blank");
    expect(links[0]).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders source type labels", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent(sampleReferences)],
    });

    render(<ReferencesTab />);
    expect(screen.getByText("blog")).toBeInTheDocument();
    expect(screen.getByText("official")).toBeInTheDocument();
    expect(screen.getByText("github")).toBeInTheDocument();
  });

  it("renders hostname from URL", () => {
    usePipelineStore.setState({
      events: [makeResearchCompleteEvent(sampleReferences)],
    });

    render(<ReferencesTab />);
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("docs.python.org")).toBeInTheDocument();
    expect(screen.getByText("github.com")).toBeInTheDocument();
  });

  it("renders relevance scores scaled to 5", () => {
    usePipelineStore.setState({
      events: [
        makeResearchCompleteEvent([
          {
            url: "https://example.com",
            title: "High relevance",
            summary: "Very relevant",
            relevance_score: 1.0,
            source_type: "blog",
          },
        ]),
      ],
    });

    render(<ReferencesTab />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });
});
