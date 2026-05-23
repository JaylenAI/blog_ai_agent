import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ValidationTab } from "../tabs/ValidationTab";
import { usePipelineStore } from "../../stores/pipeline-store";
import type { ValidationItem, ValidationSummary } from "../../types/pipeline";

function makeSummary(overrides: Partial<ValidationSummary> = {}): ValidationSummary {
  return {
    total: 10,
    passed: 8,
    failed: 2,
    score: 0.85,
    by_category: {},
    ...overrides,
  };
}

function makeValidation(overrides: Partial<ValidationItem> = {}): ValidationItem {
  return {
    category: "seo",
    item: "제목 길이",
    passed: true,
    score: 0.9,
    message: "적절한 길이",
    ...overrides,
  };
}

describe("ValidationTab", () => {
  beforeEach(() => {
    usePipelineStore.setState({
      validations: [],
      validationSummary: null,
    });
  });

  it("renders empty state when no validation summary", () => {
    render(<ValidationTab />);
    expect(screen.getByText("검증 결과 없음")).toBeInTheDocument();
  });

  it("renders empty state container with correct class", () => {
    const { container } = render(<ValidationTab />);
    expect(container.querySelector(".empty")).toBeInTheDocument();
  });

  it("renders summary scores when validation summary exists", () => {
    usePipelineStore.setState({
      validations: [],
      validationSummary: makeSummary({ passed: 8, failed: 2, score: 0.85 }),
    });

    render(<ValidationTab />);
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("renders PASS and WARN labels", () => {
    usePipelineStore.setState({
      validations: [],
      validationSummary: makeSummary(),
    });

    render(<ValidationTab />);
    expect(screen.getByText("PASS")).toBeInTheDocument();
    expect(screen.getByText("WARN")).toBeInTheDocument();
  });

  it("renders validation items grouped by category", () => {
    usePipelineStore.setState({
      validations: [
        makeValidation({ category: "seo", item: "메타 디스크립션", passed: true, score: 1.0 }),
        makeValidation({ category: "seo", item: "H1 태그", passed: false, score: 0.3 }),
        makeValidation({ category: "aeo", item: "FAQ 구조", passed: true, score: 0.95 }),
      ],
      validationSummary: makeSummary(),
    });

    render(<ValidationTab />);
    expect(screen.getByText("SEO")).toBeInTheDocument();
    expect(screen.getByText("AEO")).toBeInTheDocument();
    expect(screen.getByText("메타 디스크립션")).toBeInTheDocument();
    expect(screen.getByText("H1 태그")).toBeInTheDocument();
    expect(screen.getByText("FAQ 구조")).toBeInTheDocument();
  });

  it("renders pass and warn classes for validation items", () => {
    usePipelineStore.setState({
      validations: [
        makeValidation({ category: "seo", item: "통과 항목", passed: true, score: 1.0 }),
        makeValidation({ category: "seo", item: "경고 항목", passed: false, score: 0.2 }),
      ],
      validationSummary: makeSummary(),
    });

    const { container } = render(<ValidationTab />);
    const passRows = container.querySelectorAll(".vl-row.pass");
    const warnRows = container.querySelectorAll(".vl-row.warn");
    expect(passRows.length).toBe(1);
    expect(warnRows.length).toBe(1);
  });

  it("renders individual score percentages", () => {
    usePipelineStore.setState({
      validations: [
        makeValidation({ category: "geo", item: "키워드 밀도", passed: true, score: 0.72 }),
      ],
      validationSummary: makeSummary(),
    });

    render(<ValidationTab />);
    expect(screen.getByText("72%")).toBeInTheDocument();
  });

  it("renders style category with item count pill", () => {
    usePipelineStore.setState({
      validations: [
        makeValidation({ category: "style", item: "글자수", passed: true, score: 1.0 }),
        makeValidation({ category: "style", item: "톤", passed: true, score: 0.9 }),
      ],
      validationSummary: makeSummary(),
    });

    render(<ValidationTab />);
    expect(screen.getByText("STYLE.MD 양식")).toBeInTheDocument();
    expect(screen.getByText("2항목")).toBeInTheDocument();
  });
});
