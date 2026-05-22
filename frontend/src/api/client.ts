import type { ApiResponse, Article } from "../types/article";
import type { BlogFormat, FormatSuggestion } from "../types/format";
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
    create: (topic: string, title?: string, formatId?: string) =>
      request<Article>("/articles", {
        method: "POST",
        body: JSON.stringify({ topic, title, format_id: formatId }),
      }),
    getContent: (id: number) => requestText(`/articles/${id}/content`),
    listImages: (id: number) =>
      request<string[]>(`/articles/${id}/images`),
    imageUrl: (id: number, filename: string) =>
      `${BASE_URL}/articles/${id}/images/${encodeURIComponent(filename)}`,
    delete: (id: number) =>
      request<{ deleted: boolean }>(`/articles/${id}`, { method: "DELETE" }),
    updateContent: (id: number, content: string) =>
      request<{ word_count: number }>(`/articles/${id}/content`, {
        method: "PUT",
        body: JSON.stringify({ content }),
      }),
    saveObsidian: (id: number) =>
      request<{ success: boolean; path?: string }>(`/articles/${id}/save-obsidian`, {
        method: "POST",
      }),
    listVersions: (id: number) =>
      request<{ version_id: string; timestamp: string; size: number; word_count: number }[]>(
        `/articles/${id}/versions`,
      ),
    getVersionContent: (id: number, versionId: string) =>
      requestText(`/articles/${id}/versions/${versionId}`),
    restoreVersion: (id: number, versionId: string) =>
      request<{ restored: boolean; word_count: number }>(
        `/articles/${id}/versions/${versionId}/restore`,
        { method: "POST" },
      ),
    update: (id: number, data: { title?: string; category?: string; status?: string }) =>
      request<Article>(`/articles/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
  },

  publishKit: {
    get: (id: number) =>
      request<{
        title: string;
        category: string;
        tags: string[];
        markdown: string | null;
        html: string | null;
        images: { name: string; url: string }[];
        diagrams: { name: string; content: string }[];
        word_count: number;
        status: string;
      }>(`/articles/${id}/publish-kit`),
  },

  formats: {
    list: () => request<BlogFormat[]>("/formats"),
    suggest: (topic: string) =>
      request<FormatSuggestion[]>(
        `/formats/suggest?topic=${encodeURIComponent(topic)}`,
      ),
  },

  pipeline: {
    start: (articleId: number, autoGateOne = false, formatId?: string) =>
      request<{ events: PipelineEvent[]; run_id: number }>("/pipeline/start", {
        method: "POST",
        body: JSON.stringify({
          article_id: articleId,
          auto_gate_one: autoGateOne,
          format_id: formatId,
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
    cancel: (runId: number) =>
      request<{ status: string }>(`/pipeline/runs/${runId}/cancel`, {
        method: "POST",
      }),
    listRuns: (articleId?: number, limit = 20, offset = 0) => {
      const params = new URLSearchParams();
      if (articleId != null) params.set("article_id", String(articleId));
      params.set("limit", String(limit));
      params.set("offset", String(offset));
      return request<PipelineRun[]>(`/pipeline/runs?${params}`);
    },
  },

  settings: {
    getStyleGuide: () => requestText("/settings/style-guide"),
    getObsidian: () =>
      request<{ vault_path: string; frontmatter_tags: string[]; auto_save: boolean }>("/settings/obsidian"),
    updateObsidian: (data: { vault_path: string; frontmatter_tags: string[]; auto_save: boolean }) =>
      request<typeof data>("/settings/obsidian", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    getGeneral: () =>
      request<{
        tistory_blog_url: string;
        stage_timeout: number;
        image_generation_enabled: boolean;
        max_images_per_article: number;
        log_level: string;
      }>("/settings/general"),
    updateGeneral: (data: {
      tistory_blog_url: string;
      stage_timeout: number;
      image_generation_enabled: boolean;
      max_images_per_article: number;
      log_level: string;
    }) =>
      request<typeof data>("/settings/general", {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    batchUpdate: (data: { article_ids: number[]; category?: string; tags?: string[]; status?: string }) =>
      request<{ updated: number }>("/settings/batch-update", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};
