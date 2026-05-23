import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

import { api } from "../client";
import { ApiError, NetworkError } from "../errors";

beforeEach(() => {
  mockFetch.mockReset();
});

function jsonResponse(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: "OK",
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
    headers: new Headers(),
    body: null,
    redirected: false,
    type: "basic",
    url: "",
    clone: () => jsonResponse(data, status) as Response,
    bodyUsed: false,
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
    blob: () => Promise.resolve(new Blob()),
    formData: () => Promise.resolve(new FormData()),
    bytes: () => Promise.resolve(new Uint8Array()),
  } as Response;
}

function textResponse(text: string, status = 200): Response {
  return {
    ...jsonResponse(null, status),
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(text),
  } as Response;
}

describe("api.articles", () => {
  it("list fetches with default pagination", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { items: [], total: 0, page: 1, limit: 20 } }),
    );
    const res = await api.articles.list();
    expect(res.success).toBe(true);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/articles?page=1&limit=20"),
      expect.any(Object),
    );
  });

  it("list passes custom page and limit", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { items: [], total: 0, page: 3, limit: 10 } }),
    );
    await api.articles.list(3, 10);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/articles?page=3&limit=10"),
      expect.any(Object),
    );
  });

  it("get fetches a single article", async () => {
    const article = { id: 1, topic: "test" };
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: article }),
    );
    const res = await api.articles.get(1);
    expect(res.data).toEqual(article);
  });

  it("create sends POST with topic", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { id: 1, topic: "MCP" } }),
    );
    await api.articles.create("MCP", "제목", "concept");
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("POST");
    const body = JSON.parse(opts.body);
    expect(body.topic).toBe("MCP");
    expect(body.title).toBe("제목");
    expect(body.format_id).toBe("concept");
  });

  it("delete sends DELETE request", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { deleted: true } }),
    );
    await api.articles.delete(5);
    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain("/articles/5");
    expect(opts.method).toBe("DELETE");
  });

  it("updateContent sends PUT with content", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { word_count: 100 } }),
    );
    await api.articles.updateContent(1, "새 내용");
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PUT");
    expect(JSON.parse(opts.body).content).toBe("새 내용");
  });

  it("getContent returns text", async () => {
    mockFetch.mockResolvedValueOnce(textResponse("# 마크다운"));
    const result = await api.articles.getContent(1);
    expect(result).toBe("# 마크다운");
  });

  it("getContent returns null on 404", async () => {
    mockFetch.mockResolvedValueOnce(textResponse("", 404));
    const result = await api.articles.getContent(1);
    expect(result).toBeNull();
  });

  it("getHtml returns text", async () => {
    mockFetch.mockResolvedValueOnce(textResponse("<h1>test</h1>"));
    const result = await api.articles.getHtml(1);
    expect(result).toBe("<h1>test</h1>");
  });

  it("imageUrl constructs correct URL", () => {
    const url = api.articles.imageUrl(1, "thumb.png");
    expect(url).toContain("/articles/1/images/thumb.png");
  });

  it("imageUrl encodes special characters", () => {
    const url = api.articles.imageUrl(1, "이미지 파일.png");
    expect(url).toContain(encodeURIComponent("이미지 파일.png"));
  });

  it("saveObsidian sends POST", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { success: true, path: "/vault/test.md" } }),
    );
    const res = await api.articles.saveObsidian(1);
    expect(res.data).toEqual({ success: true, path: "/vault/test.md" });
  });

  it("update sends PATCH with data", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { id: 1, title: "변경됨" } }),
    );
    await api.articles.update(1, { title: "변경됨" });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PATCH");
  });
});

describe("api.formats", () => {
  it("list fetches formats", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: [{ id: "concept", name: "개념형" }] }),
    );
    const res = await api.formats.list();
    expect(res.success).toBe(true);
  });

  it("suggest encodes topic", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: [] }),
    );
    await api.formats.suggest("MCP 서버");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining(encodeURIComponent("MCP 서버")),
      expect.any(Object),
    );
  });
});

describe("api.pipeline", () => {
  it("start sends POST with body", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { events: [], run_id: 1 } }),
    );
    await api.pipeline.start(1, true, "tutorial");
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("POST");
    const body = JSON.parse(opts.body);
    expect(body.article_id).toBe(1);
    expect(body.auto_gate_one).toBe(true);
    expect(body.format_id).toBe("tutorial");
  });

  it("approve sends POST to correct URL", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { events: [] } }),
    );
    await api.pipeline.approve(42);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/pipeline/runs/42/approve"),
      expect.any(Object),
    );
  });

  it("reject sends POST", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { status: "cancelled" } }),
    );
    await api.pipeline.reject(42);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/pipeline/runs/42/reject"),
      expect.any(Object),
    );
  });

  it("cancel sends POST", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { status: "cancelled" } }),
    );
    await api.pipeline.cancel(10);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("/pipeline/runs/10/cancel");
  });

  it("listRuns builds query params", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: [] }),
    );
    await api.pipeline.listRuns(5, 10, 20);
    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("article_id=5");
    expect(url).toContain("limit=10");
    expect(url).toContain("offset=20");
  });

  it("listRuns omits article_id when null", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: [] }),
    );
    await api.pipeline.listRuns(undefined, 20, 0);
    const [url] = mockFetch.mock.calls[0];
    expect(url).not.toContain("article_id");
  });
});

describe("api.settings", () => {
  it("getStyleGuide returns text", async () => {
    mockFetch.mockResolvedValueOnce(textResponse("# 스타일 가이드"));
    const result = await api.settings.getStyleGuide();
    expect(result).toBe("# 스타일 가이드");
  });

  it("updateObsidian sends PUT", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { vault_path: "/v" } }),
    );
    await api.settings.updateObsidian({
      vault_path: "/v",
      frontmatter_tags: [],
      auto_save: false,
    });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("PUT");
  });

  it("batchUpdate sends POST", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ success: true, data: { updated: 3 } }),
    );
    await api.settings.batchUpdate({ article_ids: [1, 2, 3], category: "AI" });
    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.method).toBe("POST");
  });
});

describe("error handling", () => {
  it("throws NetworkError on fetch failure", async () => {
    mockFetch.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    await expect(api.articles.list()).rejects.toThrow(NetworkError);
  });

  it("throws ApiError on non-ok response", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ error: "권한 없음" }, 403),
    );
    await expect(api.articles.list()).rejects.toThrow(ApiError);
  });

  it("ApiError contains status code", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ error: "서버 오류" }, 500),
    );
    try {
      await api.articles.list();
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      expect((e as ApiError).status).toBe(500);
      expect((e as ApiError).isServerError).toBe(true);
    }
  });

  it("ApiError parses error message from body", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ error: "중복된 항목" }, 409),
    );
    try {
      await api.articles.list();
    } catch (e) {
      expect((e as ApiError).message).toBe("중복된 항목");
    }
  });

  it("NetworkError on requestText fetch failure", async () => {
    mockFetch.mockRejectedValueOnce(new TypeError("network down"));
    await expect(api.articles.getContent(1)).rejects.toThrow(NetworkError);
  });
});

describe("ApiError class", () => {
  it("isNotFound returns true for 404", () => {
    const err = new ApiError(404, "Not found");
    expect(err.isNotFound).toBe(true);
    expect(err.isServerError).toBe(false);
  });

  it("isServerError returns true for 500+", () => {
    expect(new ApiError(500, "err").isServerError).toBe(true);
    expect(new ApiError(503, "err").isServerError).toBe(true);
    expect(new ApiError(499, "err").isServerError).toBe(false);
  });

  it("name is ApiError", () => {
    expect(new ApiError(400, "bad").name).toBe("ApiError");
  });
});

describe("NetworkError class", () => {
  it("has default message", () => {
    expect(new NetworkError().message).toBe("네트워크 연결을 확인해주세요");
  });

  it("accepts custom message", () => {
    expect(new NetworkError("custom").message).toBe("custom");
  });

  it("name is NetworkError", () => {
    expect(new NetworkError().name).toBe("NetworkError");
  });
});
