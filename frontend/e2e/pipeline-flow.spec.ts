import { test, expect } from "@playwright/test";
import { mockArticleAPIs, SSE_EVENTS } from "./fixtures";

test.describe("파이프라인 SSE 플로우", () => {
  test.beforeEach(async ({ page }) => {
    await mockArticleAPIs(page);
  });

  test("주제 입력 후 파이프라인이 시작되고 Gate 1에서 멈춘다", async ({
    page,
  }) => {
    await page.route("**/api/v1/pipeline/start/stream", (route) => {
      const body =
        SSE_EVENTS.stageStart("router") +
        SSE_EVENTS.stageComplete("router") +
        SSE_EVENTS.stageStart("researcher") +
        SSE_EVENTS.stageComplete("researcher") +
        SSE_EVENTS.stageStart("outliner") +
        SSE_EVENTS.stageComplete("outliner") +
        SSE_EVENTS.gatePending("gate_one");

      return route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body,
      });
    });

    await page.goto("/");

    await page.locator("textarea").fill("AI란 무엇인가?");
    await page.getByRole("button", { name: /생성 시작/ }).click();

    await expect(
      page.locator('text=GATE 1').first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test("파이프라인 에러 시 에러 메시지가 표시된다", async ({ page }) => {
    await page.route("**/api/v1/pipeline/start/stream", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: SSE_EVENTS.stageError("Claude CLI 연결 실패"),
      }),
    );

    await page.goto("/");

    await page.locator("textarea").fill("테스트 주제");
    await page.getByRole("button", { name: /생성 시작/ }).click();

    await expect(
      page.locator('text=Claude CLI 연결 실패').first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test("Gate 1 승인 후 Gate 2까지 진행된다", async ({ page }) => {
    await page.route("**/api/v1/pipeline/start/stream", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          SSE_EVENTS.stageStart("router") +
          SSE_EVENTS.stageComplete("router") +
          SSE_EVENTS.stageStart("researcher") +
          SSE_EVENTS.stageComplete("researcher") +
          SSE_EVENTS.stageStart("outliner") +
          SSE_EVENTS.stageComplete("outliner") +
          SSE_EVENTS.gatePending("gate_one"),
      }),
    );

    await page.route("**/api/v1/pipeline/runs/1/approve/stream", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body:
          SSE_EVENTS.stageStart("generator") +
          SSE_EVENTS.stageComplete("generator") +
          SSE_EVENTS.stageStart("validator") +
          SSE_EVENTS.stageComplete("validator") +
          SSE_EVENTS.gatePending("gate_two"),
      }),
    );

    await page.route("**/api/v1/articles/1/content", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/plain",
        body: "# AI란 무엇인가?\n\n본문 내용입니다.",
      }),
    );

    await page.goto("/");

    await page.locator("textarea").fill("AI란 무엇인가?");
    await page.getByRole("button", { name: /생성 시작/ }).click();

    await expect(
      page.locator('text=GATE 1').first(),
    ).toBeVisible({ timeout: 10000 });

    const approveBtn = page.locator('button:has-text("본문 생성 시작")');
    await approveBtn.click();

    await expect(
      page.locator('text=GATE 2').first(),
    ).toBeVisible({ timeout: 10000 });
  });
});
