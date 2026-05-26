import type { ApiResponse, Article } from "../types/article";
import type { BlogFormat, FormatSuggestion } from "../types/format";
import type {
  PipelineEvent,
  PipelineRun,
  ValidationItem,
  ValidationSummary,
} from "../types/pipeline";
import type {
  PublishKit,
  ReferenceItem,
  ObsidianSettings,
  GeneralSettings,
  BatchUpdateRequest,
} from "../types/publish";
import { ApiError, NetworkError } from "./errors";
import type { z } from "zod";
import {
  ArticleSchema,
  ArticleListSchema,
  PipelineRunSchema,
  ValidationResultSchema,
  BlogFormatSchema,
  FormatSuggestionSchema,
  PublishKitSchema,
  ReferenceItemSchema,
  ObsidianSettingsSchema,
  GeneralSettingsSchema,
} from "./schemas";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function request<T>(
  path: string,
  options: RequestInit = {},
  schema?: z.ZodType<T>,
): Promise<ApiResponse<T>> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
  } catch {
    throw new NetworkError();
  }

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.error) message = body.error;
    } catch { /* ignore parse failure */ }
    throw new ApiError(res.status, message);
  }

  const json = (await res.json()) as ApiResponse<T>;

  if (schema && json.data != null) {
    const result = schema.safeParse(json.data);
    if (!result.success) {
      if (import.meta.env.DEV) {
        console.warn("[API] validation failed:", path, result.error.issues);
      }
    } else {
      return { ...json, data: result.data };
    }
  }

  return json;
}

async function requestText(path: string): Promise<string | null> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`);
  } catch {
    throw new NetworkError();
  }
  if (!res.ok) return null;
  return res.text();
}

export const api = {
  articles: {
    list: (page = 1, limit = 20) =>
      request<{ items: Article[]; total: number; page: number; limit: number }>(
        `/articles?page=${page}&limit=${limit}`,
        {},
        ArticleListSchema,
      ),
    get: (id: number) => request<Article>(`/articles/${id}`, {}, ArticleSchema),
    create: (topic: string, title?: string, formatId?: string) =>
      request<Article>("/articles", {
        method: "POST",
        body: JSON.stringify({ topic, title, format_id: formatId }),
      }, ArticleSchema),
    getContent: (id: number) => requestText(`/articles/${id}/content`),
    getHtml: (id: number) => requestText(`/articles/${id}/html`),
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
    update: (id: number, data: { title?: string; category?: string; status?: string; tags?: string[] }) =>
      request<Article>(`/articles/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }, ArticleSchema),
    getReferences: (id: number) =>
      request<ReferenceItem[]>(`/articles/${id}/references`, {}, ReferenceItemSchema.array()),
  },

  publishKit: {
    get: (id: number) => request<PublishKit>(`/articles/${id}/publish-kit`, {}, PublishKitSchema),
  },

  formats: {
    list: () => request<BlogFormat[]>("/formats", {}, BlogFormatSchema.array()),
    suggest: (topic: string) =>
      request<FormatSuggestion[]>(
        `/formats/suggest?topic=${encodeURIComponent(topic)}`,
        {},
        FormatSuggestionSchema.array(),
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
    getRun: (runId: number) => request<PipelineRun>(`/pipeline/runs/${runId}`, {}, PipelineRunSchema),
    getActiveRun: () =>
      request<PipelineRun | null>("/pipeline/runs/active", {}, PipelineRunSchema.nullable()),
    getValidations: (runId: number) =>
      request<{ validations: ValidationItem[]; summary: ValidationSummary }>(
        `/pipeline/runs/${runId}/validations`,
        {},
        ValidationResultSchema,
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
      return request<PipelineRun[]>(`/pipeline/runs?${params}`, {}, PipelineRunSchema.array());
    },
  },

  settings: {
    getStyleGuide: () => requestText("/settings/style-guide"),
    getObsidian: () =>
      request<ObsidianSettings>("/settings/obsidian", {}, ObsidianSettingsSchema),
    updateObsidian: (data: ObsidianSettings) =>
      request<ObsidianSettings>("/settings/obsidian", {
        method: "PUT",
        body: JSON.stringify(data),
      }, ObsidianSettingsSchema),
    getGeneral: () =>
      request<GeneralSettings>("/settings/general", {}, GeneralSettingsSchema),
    updateGeneral: (data: GeneralSettings) =>
      request<GeneralSettings>("/settings/general", {
        method: "PUT",
        body: JSON.stringify(data),
      }, GeneralSettingsSchema),
    batchUpdate: (data: BatchUpdateRequest) =>
      request<{ updated: number }>("/settings/batch-update", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};
