import { test, expect } from "@playwright/test";

test.describe.configure({ mode: "serial" });

const API = "http://localhost:8000/api/v1";

async function isBackendUp(request: import("@playwright/test").APIRequestContext) {
  try {
    const res = await request.get(`${API}/../health`, { timeout: 3000 });
    // 429(rate limit)도 서버가 살아있다는 증거 — 다운으로 오판하지 않는다.
    return res.ok() || res.status() === 429;
  } catch {
    return false;
  }
}

test.describe("Phase 6 — Calendar API", () => {
  test("GET /calendar returns article list", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/calendar`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
    }
  });

  test("PUT /calendar/:id/schedule sets scheduled_at", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const listRes = await request.get(`${API}/calendar`);
    if (listRes.status() !== 200) return;
    const articles = (await listRes.json()).data;
    if (articles.length === 0) return;

    const articleId = articles[0].article_id;
    const res = await request.put(`${API}/calendar/${articleId}/schedule`, {
      data: { scheduled_at: "2026-07-01T09:00:00" },
    });
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.scheduled_at).toContain("2026-07-01");
    }
  });

  test("DELETE /calendar/:id/schedule clears scheduled_at", async ({
    request,
  }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const listRes = await request.get(`${API}/calendar`);
    if (listRes.status() !== 200) return;
    const articles = (await listRes.json()).data;
    if (articles.length === 0) return;

    const articleId = articles[0].article_id;
    const res = await request.delete(`${API}/calendar/${articleId}/schedule`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.scheduled_at).toBeNull();
    }
  });

  test("PUT /calendar/9999/schedule returns not found", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.put(`${API}/calendar/9999/schedule`, {
      data: { scheduled_at: "2026-07-01T09:00:00" },
    });
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(false);
    }
  });
});

test.describe("Phase 6 — Webhooks API", () => {
  test("GET /webhooks returns list", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/webhooks`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
    }
  });

  test("POST /webhooks creates webhook", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.post(`${API}/webhooks`, {
      data: {
        url: "https://example.com/test-hook",
        events: ["pipeline_complete"],
        name: "e2e-test-hook",
      },
    });
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.name).toBe("e2e-test-hook");
      expect(body.data.active).toBe(true);
    }
  });

  test("PATCH /webhooks/:id/toggle toggles active state", async ({
    request,
  }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const listRes = await request.get(`${API}/webhooks`);
    if (listRes.status() !== 200) return;
    const hooks = (await listRes.json()).data;
    if (hooks.length === 0) return;

    const hookId = hooks[hooks.length - 1].id;
    const res = await request.patch(`${API}/webhooks/${hookId}/toggle`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.active).toBe(false);
    }
  });

  test("DELETE /webhooks/:id removes webhook", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const listRes = await request.get(`${API}/webhooks`);
    if (listRes.status() !== 200) return;
    const hooks = (await listRes.json()).data;
    if (hooks.length === 0) return;

    const hookId = hooks[hooks.length - 1].id;
    const res = await request.delete(`${API}/webhooks/${hookId}`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
    }
  });

  test("DELETE /webhooks/9999 returns not found", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.delete(`${API}/webhooks/9999`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(false);
    }
  });
});

test.describe("Phase 6 — Brand Persona API", () => {
  test("GET /settings/brand-persona returns defaults", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/settings/brand-persona`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty("name");
      expect(body.data).toHaveProperty("tone");
      expect(body.data).toHaveProperty("writing_style");
      expect(body.data).toHaveProperty("first_person");
    }
  });

  test("PUT /settings/brand-persona updates persona", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.put(`${API}/settings/brand-persona`, {
      data: {
        name: "E2E 테스트",
        tone: "반말체",
        writing_style: "캐주얼",
        target_audience: "초보자",
        vocabulary_level: "초급",
        emoji_usage: true,
        first_person: "나",
      },
    });
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.name).toBe("E2E 테스트");
      expect(body.data.emoji_usage).toBe(true);
    }
  });

  test("GET /settings/brand-persona returns updated values", async ({
    request,
  }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/settings/brand-persona`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.data.name).toBe("E2E 테스트");
    }
  });

  test("PUT /settings/brand-persona restores defaults", async ({
    request,
  }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    await request.put(`${API}/settings/brand-persona`, {
      data: {
        name: "기본",
        tone: "격식체",
        writing_style: "기술 블로그 전문가",
        target_audience: "AI/개발 분야 종사자",
        vocabulary_level: "전문가",
        emoji_usage: false,
        first_person: "필자",
      },
    });
  });
});

test.describe("Phase 6 — Publisher Registry & Settings", () => {
  test("GET /settings/general returns settings", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/settings/general`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty("tistory_blog_url");
    }
  });

  test("GET /settings/obsidian returns settings", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/settings/obsidian`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data).toHaveProperty("vault_path");
    }
  });

  test("GET /settings/style-guide returns content", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/settings/style-guide`);
    expect([200, 429]).toContain(res.status());
  });
});
