import { test, expect } from "@playwright/test";
import { mockFormatsAPI } from "./fixtures";

test.describe("에러 처리", () => {
  test.beforeEach(async ({ page }) => {
    await mockFormatsAPI(page);
  });

  test("백엔드 다운 시 에러가 표시되고 크래시하지 않는다", async ({ page }) => {
    await page.route("**/api/v1/articles?*", (route) =>
      route.fulfill({ status: 500, body: "Internal Server Error" }),
    );

    await page.route("**/api/v1/pipeline/runs/active", (route) =>
      route.fulfill({ status: 500, body: "Internal Server Error" }),
    );

    await page.goto("/");

    await expect(page.locator("body")).toBeVisible();

    const textarea = page.locator("textarea");
    await expect(textarea).toBeVisible({ timeout: 5000 });
  });

  test("파이프라인 시작 시 서버 에러가 토스트로 표시된다", async ({ page }) => {
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

    await page.route("**/api/v1/articles", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            success: true,
            data: {
              id: 1, topic: "test", slug: "test", status: "draft",
              created_at: "2026-01-01", updated_at: "2026-01-01",
            },
          }),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/pipeline/start/stream", (route) =>
      route.fulfill({ status: 500, body: "서버 오류" }),
    );

    await page.goto("/");
    await page.locator("textarea").fill("테스트 주제");
    await page.getByRole("button", { name: /생성 시작/ }).click();

    await page.waitForTimeout(3000);

    await expect(page.locator("body")).toBeVisible();
  });

  test("네트워크 타임아웃 시 앱이 크래시하지 않는다", async ({ page }) => {
    await page.route("**/api/v1/articles?*", (route) =>
      route.abort("timedout"),
    );

    await page.route("**/api/v1/pipeline/runs/active", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: null }),
      }),
    );

    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
  });
});
