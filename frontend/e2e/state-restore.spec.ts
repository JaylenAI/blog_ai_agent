import { test, expect } from "@playwright/test";

test.describe("페이지 새로고침 상태 복원", () => {
  test("활성 run이 없으면 Launcher가 표시된다", async ({ page }) => {
    await page.route("**/api/v1/articles?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { items: [], total: 0, page: 1, limit: 20 },
        }),
      }),
    );

    await page.route("**/api/v1/pipeline/runs/active", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: null }),
      }),
    );

    await page.goto("/");

    const input = page.locator(
      'input[placeholder], textarea[placeholder]',
    ).first();
    await expect(input).toBeVisible({ timeout: 5000 });
  });

  test("paused 상태 run이 있으면 Gate 모달이 표시된다", async ({ page }) => {
    await page.route("**/api/v1/articles?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: { items: [], total: 0, page: 1, limit: 20 },
        }),
      }),
    );

    await page.route("**/api/v1/pipeline/runs/active", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            article_id: 1,
            current_stage: "gate_one",
            status: "paused",
            started_at: "2026-05-21T00:00:00",
            completed_at: null,
          },
        }),
      }),
    );

    await page.route("**/api/v1/articles/1", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            id: 1,
            topic: "복원 테스트",
            title: "복원 테스트",
            slug: "복원-테스트",
            status: "draft",
            created_at: "2026-05-21T00:00:00",
            updated_at: "2026-05-21T00:00:00",
          },
        }),
      }),
    );

    await page.goto("/");

    await expect(
      page.locator('text=GATE 1').first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
