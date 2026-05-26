export type PipelineMode =
  | "idle"
  | "research"
  | "outline"
  | "generate"
  | "validate"
  | "gate2"
  | "published";

export type EventType =
  | "stage_start"
  | "stage_complete"
  | "stage_progress"
  | "stage_error"
  | "gate_pending"
  | "pipeline_complete"
  | "pipeline_error";

export interface PipelineEvent {
  event_type: EventType;
  stage: string;
  message: string;
  data: Record<string, unknown>;
}

export interface ValidationItem {
  category: "style" | "seo" | "aeo" | "geo";
  item: string;
  passed: boolean;
  score: number;
  message: string;
}

export interface ValidationSummary {
  total: number;
  passed: number;
  failed: number;
  score: number;
  by_category: Record<string, { total: number; passed: number }>;
}

export interface PipelineRun {
  id: number;
  article_id: number;
  current_stage: string;
  status: string;
  error_message?: string;
  started_at: string;
  completed_at: string | null;
}
