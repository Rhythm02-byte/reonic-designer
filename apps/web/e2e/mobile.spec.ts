import { test, expect, kwpShown, noHorizontalScroll } from "./fixtures";

test("planner has no horizontal scroll at 375px", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Design for/ })).toBeVisible();
  await expect.poll(() => kwpShown(page), { timeout: 60_000 }).toBeGreaterThan(0);
  expect(await noHorizontalScroll(page)).toBe(true);
});

test("offer has no horizontal scroll at 375px", async ({ page }) => {
  await page.goto("/");
  const share = page.getByRole("button", { name: /Share with homeowner/ });
  await expect(share).toBeEnabled();
  await share.click();
  const href = await page.getByRole("dialog").getByRole("link", { name: /Open view/ }).getAttribute("href");
  await page.goto(href!);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(await noHorizontalScroll(page)).toBe(true);
});
