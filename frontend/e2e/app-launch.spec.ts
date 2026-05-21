import { test, expect } from "@playwright/test";
import { mockArticleAPIs } from "./fixtures";

test.describe("앱 초기 로딩", () => {
  test.beforeEach(async ({ page }) => {
    await mockArticleAPIs(page);
  });

  test("메인 페이지가 정상 로딩된다", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
  });

  test("Launcher 주제 입력 textarea가 표시된다", async ({ page }) => {
    await page.goto("/");
    const textarea = page.locator("textarea");
    await expect(textarea).toBeVisible({ timeout: 5000 });
  });

  test("생성 시작 버튼이 존재하고 비활성화 상태이다", async ({ page }) => {
    await page.goto("/");
    const btn = page.getByRole("button", { name: /생성 시작/ });
    await expect(btn).toBeVisible({ timeout: 5000 });
    await expect(btn).toBeDisabled();
  });

  test("주제 입력 시 생성 시작 버튼이 활성화된다", async ({ page }) => {
    await page.goto("/");
    const textarea = page.locator("textarea");
    await textarea.fill("테스트 주제");
    const btn = page.getByRole("button", { name: /생성 시작/ });
    await expect(btn).toBeEnabled();
  });
});
