import { test, expect, pvKwp, kwpShown } from "./fixtures";

test.describe("planner", () => {
  test("loads with a design, edit shows What changed, undo restores", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /Design for/ })).toBeVisible();
    await expect.poll(() => kwpShown(page), { timeout: 60_000 }).toBeGreaterThan(0);
    const before = await pvKwp(page);
    expect(before).toBeGreaterThan(0);

    const use = page.getByLabel("Annual electricity use");
    const original = await use.inputValue();
    await use.fill("12000");
    await use.press("Enter");
    const changed = page.getByRole("status").filter({ hasText: "What changed?" });
    await expect(changed).toBeVisible();
    await expect(changed).toContainText("Annual electricity use");
    await expect.poll(() => pvKwp(page)).not.toBe(before);

    await page.getByRole("button", { name: "Undo" }).click();
    await expect(use).toHaveValue(original);
    await expect.poll(() => pvKwp(page)).toBe(before);
    await expect(page.getByRole("button", { name: "Undo" })).toHaveCount(0);
  });

  test("custom dropdown: click, keyboard, Escape", async ({ page }) => {
    await page.setViewportSize({ width: 1000, height: 800 }); // below xl the header Customer select shows
    await page.goto("/");
    const select = page.getByRole("combobox", { name: "Customer" });
    await expect(select).toBeVisible();
    await expect(select).toHaveAttribute("aria-haspopup", "listbox");
    const first = (await select.innerText()).trim();

    await select.click();
    await expect(page.getByRole("listbox")).toBeVisible();
    await expect(page.getByRole("option").first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("listbox")).toHaveCount(0);
    await expect(select).toHaveText(first);

    await select.focus();
    await select.press("ArrowDown"); // opens
    await expect(page.getByRole("listbox")).toBeVisible();
    await select.press("ArrowDown");
    await select.press("Enter");
    await expect(page.getByRole("listbox")).toHaveCount(0);
    await expect(select).not.toHaveText(first);
  });

  test("Ask next answer changes the inputs", async ({ page }) => {
    await page.goto("/");
    const ask = page.getByRole("region", { name: "Ask the customer next" });
    await expect(ask).toBeVisible();
    const group = ask.getByRole("group").first();
    const question = (await group.getAttribute("aria-label"))!;
    await group.getByRole("button").first().click();
    await expect(page.getByRole("status").filter({ hasText: "What changed?" })).toBeVisible();
    // Answered questions are not asked again.
    await expect(ask.getByRole("group", { name: question })).toHaveCount(0);
  });

  test("share dialog -> offer page; switching option changes parts", async ({ page, context }) => {
    await page.goto("/");
    await expect.poll(() => kwpShown(page), { timeout: 60_000 }).toBeGreaterThan(0);
    const share = page.getByRole("button", { name: /Share with homeowner/ });
    await expect(share).toBeEnabled();
    await share.click();
    const dialog = page.getByRole("dialog", { name: "Share with the homeowner" });
    await expect(dialog.getByRole("img", { name: /QR code/ })).toBeVisible();

    const link = dialog.getByRole("link", { name: /Open view/ });
    expect(await link.getAttribute("href")).toContain("/offer#");
    const popup = context.waitForEvent("page");
    await link.click();
    const offer = await popup;
    await expect(offer).toHaveURL(/\/offer#/);
    await expect(offer.getByRole("heading", { level: 1 })).toBeVisible();

    const radios = offer.locator('input[name="option"]');
    await expect(radios.first()).toBeAttached();
    expect(await radios.count()).toBeGreaterThan(1);
    const parts = offer.locator('section[aria-labelledby="parts"]'); // Faris's parts section (always open)
    const text = () => parts.innerText();
    const a = await text();
    await offer.locator("label").filter({ has: radios }).nth(1).click();
    await expect(radios.nth(1)).toBeChecked();
    await expect.poll(text).not.toBe(a);
  });
});

test.describe("pitch", () => {
  test("slide 1 renders and next advances", async ({ page }) => {
    await page.goto("/pitch");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    const next = page.getByRole("button", { name: "Next" }).first();
    await expect(next).toBeVisible();
    const start = () => new URL(page.url()).hash;
    const h0 = start();
    await next.click();
    await expect.poll(start).not.toBe(h0);
    expect(start()).toMatch(/^#\d/);
  });

  test("?demo=1 renders without engine", async ({ page }) => {
    await page.route("**/localhost:8000/**", (r) => r.abort());
    await page.goto("/pitch?demo=1");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByRole("button", { name: "Next" }).first()).toBeVisible();
  });
});

test.describe("other pages", () => {
  test("/lab renders its headline without running anything", async ({ page }) => {
    await page.route("**/lab/run**", (r) => r.abort()); // never score the private test split
    await page.goto("/lab");
    await expect(page.getByRole("heading").first()).toBeVisible();
  });

  test("/new-customer creates a customer with empty facts", async ({ page }) => {
    await page.goto("/new-customer");
    await page.getByLabel("Customer name").fill("E2E Testfamilie");
    await page.getByRole("button", { name: /Next: pick house|Continue to location/ }).click();
    await page.getByRole("button", { name: /Create customer/ }).click();
    await expect(page).toHaveURL(/localhost:3000\/$/);
    await expect(page.getByRole("heading", { name: /Design for E2E Testfamilie/ })).toBeVisible();
    await expect(page.getByLabel("Annual electricity use")).toHaveValue("");
    await page.evaluate(() => localStorage.removeItem("rhythm.workspace.v1"));
  });
});
