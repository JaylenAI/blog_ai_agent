import { defineConfig, devices } from "@playwright/test";

// E2E 대상 포트. 다른 앱이 5173을 점유 중일 수 있으므로 환경변수로 오버라이드 가능.
// CI에서는 깨끗한 환경이라 기본값 5173을 그대로 사용한다.
const PORT = Number(process.env.E2E_PORT ?? 5173);
const HOST = process.env.E2E_HOST ?? "localhost";
const baseURL = `http://${HOST}:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    // strictPort로 지정 포트를 강제 — 점유 시 다른 포트로 밀리지 않고 명확히 실패시킨다.
    command: `pnpm dev --port ${PORT} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
