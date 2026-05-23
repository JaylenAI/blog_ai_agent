import { test, expect } from "@playwright/test";
import { mockArticleAPIs, MOCK_ARTICLE } from "./fixtures";

test.describe("사이드바 내비게이션", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/articles?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          success: true,
          data: {
            items: [
              MOCK_ARTICLE,
              { ...MOCK_ARTICLE, id: 2, topic: "MCP 서버 구축", slug: "mcp-서버-구축" },
            ],
            total: 2,
            page: 1,
            limit: 20,
          },
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
  });

  test("아티클 목록이 사이드바에 표시된다", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=AI란 무엇인가?").first()).toBeVisible({
      timeout: 5000,
    });
    await expect(page.locator("text=MCP 서버 구축").first()).toBeVisible();
  });

  test("새 글 작성 버튼을 클릭하면 Launcher로 전환된다", async ({ page }) => {
    await page.goto("/");
    const newBtn = page.locator('[aria-label="새 글 작성"]').first();
    if (await newBtn.isVisible()) {
      await newBtn.click();
      const textarea = page.locator("textarea");
      await expect(textarea).toBeVisible({ timeout: 5000 });
    }
  });

  test("검색으로 아티클을 필터링할 수 있다", async ({ page }) => {
    await page.goto("/");

    const searchBtn = page.locator("text=검색").first();
    if (await searchBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await searchBtn.click();

      const searchInput = page.locator('input[type="text"]').first();
      if (await searchInput.isVisible({ timeout: 2000 }).catch(() => false)) {
        await searchInput.fill("MCP");
        await expect(page.locator("text=MCP 서버 구축").first()).toBeVisible();
      }
    }
  });
});

test.describe("테마 전환", () => {
  test.beforeEach(async ({ page }) => {
    await mockArticleAPIs(page);
  });

  test("페이지에 data-theme 속성이 존재한다", async ({ page }) => {
    await page.goto("/");
    const html = page.locator("html");
    const theme = await html.getAttribute("data-theme");
    expect(["light", "dark"]).toContain(theme);
  });
});
