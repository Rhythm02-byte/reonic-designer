import { test as base, expect, type Page } from "@playwright/test";

// Dev-only noise that is not an app failure.
const NOISE = [/React DevTools/i, /\[HMR\]/i, /Fast Refresh/i, /instant navigation/i, /favicon/i, /Download the React/i];

/** `test` that fails when a page logs a console error or throws. */
export const test = base.extend<{ errors: string[] }>({
  errors: [
    async ({ page }, use) => {
      const errors: string[] = [];
      page.on("console", (m) => {
        if (m.type() === "error" && !NOISE.some((n) => n.test(m.text()))) errors.push(m.text().slice(0, 300));
      });
      page.on("pageerror", (e) => errors.push(`pageerror: ${e.message.slice(0, 300)}`));
      await use(errors);
      expect(errors, "console errors").toEqual([]);
    },
    { auto: true },
  ],
});
export { expect };

/** The kWp number in the first "11.6 kWp" headline of the proposed system. */
export async function pvKwp(page: Page) {
  const t = await page.getByText(/^\d+(\.\d+)? kWp$/).first().innerText();
  return Number.parseFloat(t);
}

export const kwpShown = (page: Page) => page.getByText(/^\d+(\.\d+)? kWp$/).count();

export const noHorizontalScroll = (page: Page) =>
  page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
