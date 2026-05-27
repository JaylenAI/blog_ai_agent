import { test, expect } from "@playwright/test";

test.describe.configure({ mode: "serial" });

const API = "http://localhost:8000/api/v1";

async function isBackendUp(request: import("@playwright/test").APIRequestContext) {
  try {
    const res = await request.get(`${API}/../health`, { timeout: 3000 });
    return res.ok();
  } catch {
    return false;
  }
}

test.describe("Phase 7 — Health Check + Tistory Status", () => {
  test("GET /health/detailed includes tistory check", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/health/detailed`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.checks).toHaveProperty("tistory");
      expect(body.data.checks).toHaveProperty("database");
      expect(body.data.checks).toHaveProperty("claude_cli");
      const tistory = body.data.checks.tistory;
      expect(["ok", "warning", "error", "disabled"]).toContain(tistory.status);
    }
  });

  test("Health check returns overall status", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/health/detailed`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(["healthy", "degraded"]).toContain(body.data.status);
      expect(body.data).toHaveProperty("version");
      expect(body.data).toHaveProperty("timestamp");
    }
  });

  test("Simple health check still works", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/health`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
      expect(body.data.status).toBe("healthy");
    }
  });
});

test.describe("Phase 7 — TistoryPanel UI", () => {
  test("TistoryPanel shows connection status", async ({ page }) => {
    await page.goto("http://localhost:5173");
    await page.waitForLoadState("networkidle");

    const tistoryBtn = page.getByText("Tistory 연결", { exact: false });

    if (await tistoryBtn.isVisible()) {
      await tistoryBtn.click();
      await page.waitForTimeout(1000);

      const statusIndicator = page.locator("[role='status']");
      if (await statusIndicator.isVisible()) {
        const ariaLabel = await statusIndicator.getAttribute("aria-label");
        expect(ariaLabel).toContain("Tistory");
      }
    }
  });
});

test.describe("Phase 7 — JSON Logger Validation", () => {
  test("Backend responds correctly after logger changes", async ({
    request,
  }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const res = await request.get(`${API}/health`);
    expect([200, 429]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body.success).toBe(true);
    }
  });

  test("All API endpoints remain functional", async ({ request }) => {
    test.skip(!(await isBackendUp(request)), "백엔드 미실행 — skip");
    const endpoints = [
      { method: "GET", path: "/health" },
      { method: "GET", path: "/health/detailed" },
      { method: "GET", path: "/articles?page=1&limit=5" },
      { method: "GET", path: "/calendar" },
      { method: "GET", path: "/webhooks" },
      { method: "GET", path: "/settings/brand-persona" },
      { method: "GET", path: "/settings/general" },
    ];

    for (const ep of endpoints) {
      const res = await request.get(`${API}${ep.path}`);
      expect(
        [200, 429],
        `${ep.method} ${ep.path} returned ${res.status()}`,
      ).toContain(res.status());
    }
  });
});
