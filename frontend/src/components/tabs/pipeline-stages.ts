export interface PipelineStage {
  id: string;
  key: string;
  num: number | null;
  name: string;
  desc: string;
  expected: string;
  gate?: boolean;
}

export const PIPELINE_STAGES: readonly PipelineStage[] = [
  {
    id: "router",
    key: "router",
    num: 1,
    name: "Router",
    desc: "주제 분석 · 키워드 추출 · 분량 결정",
    expected: "10~20초",
  },
  {
    id: "research",
    key: "researcher",
    num: 2,
    name: "Researcher",
    desc: "4-channel 자료수집 (병렬)",
    expected: "2~3분",
  },
  {
    id: "outline",
    key: "outliner",
    num: 3,
    name: "Outliner",
    desc: "7~9개 대섹션 + 출처 매핑",
    expected: "30~60초",
  },
  {
    id: "gate1",
    key: "gate_one",
    num: null,
    name: "Gate 1",
    desc: "사용자 아웃라인 승인",
    expected: "사람 검수",
    gate: true,
  },
  {
    id: "generate",
    key: "generator",
    num: 4,
    name: "Generator",
    desc: "본문 + Mermaid/SVG 병렬 생성",
    expected: "3~5분",
  },
  {
    id: "validate",
    key: "validator",
    num: 5,
    name: "Validator",
    desc: "14항목 + SEO/AEO/GEO + oracle",
    expected: "30~60초",
  },
  {
    id: "gate2",
    key: "gate_two",
    num: null,
    name: "Gate 2",
    desc: "최종 승인 (필수, 자동화 불가)",
    expected: "사람 검수",
    gate: true,
  },
  {
    id: "publish",
    key: "publisher",
    num: 6,
    name: "Publisher",
    desc: "md → Tistory HTML + 클립보드",
    expected: "1~2분",
  },
];
