import type { ApiResponse, Article } from "../types/article";
import type {
  PipelineEvent,
  PipelineRun,
  ValidationItem,
  ValidationSummary,
} from "../types/pipeline";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  return (await res.json()) as ApiResponse<T>;
}

async function requestText(path: string): Promise<string | null> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) return null;
  return res.text();
}

export const api = {
  articles: {
    list: (page = 1, limit = 20) =>
      request<{ items: Article[]; total: number; page: number; limit: number }>(
        `/articles?page=${page}&limit=${limit}`,
      ),
    get: (id: number) => request<Article>(`/articles/${id}`),
    create: (topic: string, title?: string) =>
      request<Article>("/articles", {
        method: "POST",
        body: JSON.stringify({ topic, title }),
      }),
    getContent: (id: number) => requestText(`/articles/${id}/content`),
    listImages: (id: number) =>
      request<string[]>(`/articles/${id}/images`),
    imageUrl: (id: number, filename: string) =>
      `${BASE_URL}/articles/${id}/images/${encodeURIComponent(filename)}`,
  },

  pipeline: {
    start: (articleId: number, autoGateOne = false) =>
      request<{ events: PipelineEvent[]; run_id: number }>("/pipeline/start", {
        method: "POST",
        body: JSON.stringify({
          article_id: articleId,
          auto_gate_one: autoGateOne,
        }),
      }),
    approve: (runId: number) =>
      request<{ events: PipelineEvent[] }>(
        `/pipeline/runs/${runId}/approve`,
        { method: "POST" },
      ),
    reject: (runId: number) =>
      request<{ status: string }>(`/pipeline/runs/${runId}/reject`, {
        method: "POST",
      }),
    getRun: (runId: number) => request<PipelineRun>(`/pipeline/runs/${runId}`),
    getActiveRun: () =>
      request<PipelineRun | null>("/pipeline/runs/active"),
    getValidations: (runId: number) =>
      request<{ validations: ValidationItem[]; summary: ValidationSummary }>(
        `/pipeline/runs/${runId}/validations`,
      ),
  },
};
