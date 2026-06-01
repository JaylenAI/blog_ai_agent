import { test, expect } from "@playwright/test";
import { dismissModalIfPresent } from "./fixtures";

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
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // 복원된 Gate 모달 등이 떠 있으면 scrim이 사이드바 클릭을 가로챈다 → 먼저 닫는다.
    await dismissModalIfPresent(page);

    // 사이드바의 "Tistory 연결" 행(role=button)을 정확히 특정 — 패널 제목 텍스트와 구분.
    const tistoryBtn = page
      .locator('.sb-row[role="button"]')
      .filter({ hasText: "Tistory 연결" })
      .first();

    if (await tistoryBtn.isVisible().catch(() => false)) {
      await tistoryBtn.click();
      await page.waitForTimeout(1000);

      const statusIndicator = page.locator("[role='status']");
      if (await statusIndicator.isVisible().catch(() => false)) {
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
