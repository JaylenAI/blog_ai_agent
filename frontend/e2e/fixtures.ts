import type { Page } from "@playwright/test";

export const MOCK_ARTICLE = {
  id: 1,
  topic: "AI란 무엇인가?",
  title: "AI란 무엇인가?",
  slug: "ai란-무엇인가",
  status: "draft",
  category: null,
  format_id: "standard",
  content_path: null,
  word_count: 0,
  image_count: 0,
  tags: [],
  reference_count: 0,
  section_count: 0,
  thumbnail_path: "",
  created_at: "2026-05-21T00:00:00",
  updated_at: "2026-05-21T00:00:00",
};

export const SSE_EVENTS = {
  stageStart: (stage: string) =>
    `data: ${JSON.stringify({ event_type: "stage_start", stage, message: `${stage} 시작`, data: { run_id: 1 } })}\n\n`,
  stageComplete: (stage: string) =>
    `data: ${JSON.stringify({ event_type: "stage_complete", stage, message: `${stage} 완료`, data: {} })}\n\n`,
  gatePending: (gate: string) =>
    `data: ${JSON.stringify({ event_type: "gate_pending", stage: gate, message: "게이트 대기", data: { run_id: 1 } })}\n\n`,
  pipelineComplete: () =>
    `data: ${JSON.stringify({ event_type: "pipeline_complete", stage: "publisher", message: "파이프라인 완료", data: {} })}\n\n`,
  stageError: (msg: string) =>
    `data: ${JSON.stringify({ event_type: "stage_error", stage: "router", message: msg, data: {} })}\n\n`,
};

export async function mockArticleAPIs(page: Page) {
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

  await page.route("**/api/v1/articles", (route) => {
    if (route.request().method() === "POST") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true, data: MOCK_ARTICLE }),
      });
    }
    return route.continue();
  });

  await page.route("**/api/v1/pipeline/runs/active", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: null }),
    }),
  );

  await mockFormatsAPI(page);
}

export async function mockFormatsAPI(page: Page) {
  await page.route("**/api/v1/formats", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [] }),
    }),
  );

  await page.route("**/api/v1/formats/suggest?*", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true, data: [] }),
    }),
  );
}
