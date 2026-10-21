import { sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

test("visitors can read the introduction and guide before signing in", async ({ page }) => {
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/");

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "A working VUEDA demo." })).toBeVisible();
    await expect(page).toHaveTitle("Widget Warehouse | A VUEDA demo");
    await expect(page.getByRole("link", { name: "Learn about VUEDA" })).toHaveAttribute("href", "https://vueda.dev/");
    await expect(page.getByRole("link", { name: "Explore the demo", exact: true })).toHaveAttribute(
        "href",
        "/sign-in/",
    );
    await page.getByRole("link", { name: "Follow the walkthrough" }).click();

    await expect(page).toHaveURL(/\/walkthrough\/$/);
    await expect(page).toHaveTitle("Demo walkthrough | Widget Warehouse");
    await expect(page.getByRole("heading", { name: "Demo walkthrough", exact: true })).toBeVisible();
    await expect(page.getByText("On-hand stock does not increase.", { exact: true })).toBeVisible();
    await page
        .getByRole("navigation", { name: "Walkthrough sections" })
        .getByRole("link", { name: "3. Approve the order" })
        .click();
    await expect(page).toHaveURL(/\/walkthrough\/#approve$/);
    await expect
        .poll(() => page.locator("#approve").evaluate((section) => section.getBoundingClientRect().top))
        .toBeLessThan(80);

    await page.goto("/sign-in/");
    await page.getByRole("link", { name: "Follow the demo walkthrough" }).click();
    const popupPromise = page.waitForEvent("popup");
    await page.getByRole("link", { name: "Open guide in a new tab" }).click();
    const guide = await popupPromise;
    await expect(guide).toHaveURL(/\/walkthrough\/$/);
    await expect(guide.getByRole("heading", { name: "Demo walkthrough", exact: true })).toBeVisible();
    await guide.close();
    expect(errors).toEqual([]);
});

test("public pages remain readable without the API", async ({ page }) => {
    await page.route("**/routes/**", (route) => route.abort());
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "A working VUEDA demo." })).toBeVisible();
    await page.getByRole("link", { name: "Follow the walkthrough" }).click();
    await expect(page.getByRole("heading", { name: "Demo walkthrough", exact: true })).toBeVisible();
    await expect(page.getByText("supervisor@widgetwarehouse.com", { exact: true })).toBeVisible();
});

test("the guide supports direct section links and narrow screens in both themes", async ({ page }, testInfo) => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto("/walkthrough/#draft");
    await expect(page).toHaveURL(/\/walkthrough\/#draft$/);
    await expect
        .poll(() => page.locator("#draft").evaluate((section) => section.getBoundingClientRect().top))
        .toBeLessThan(80);
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);
    await page.screenshot({ path: testInfo.outputPath("guide-mobile.png") });

    await page.getByRole("link", { name: "Widget Warehouse home" }).click();
    await expect(page.getByRole("heading", { name: "A working VUEDA demo." })).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);
    await page.screenshot({ path: testInfo.outputPath("home-mobile.png"), fullPage: true });
    await page.getByRole("button", { name: "Toggle color mode" }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await page.screenshot({ path: testInfo.outputPath("home-mobile-dark.png"), fullPage: true });
});

test.describe("signed-in visitors", () => {
    test.use({ storageState: sessionFor("supervisor") });

    test("can revisit the public pages and return to the application", async ({ page }, testInfo) => {
        await page.goto("/");
        await expect(page).toHaveURL(/\/$/);
        await expect(page.getByRole("main").getByRole("link", { name: "Return to dashboard" })).toBeVisible();
        await page.screenshot({ path: testInfo.outputPath("home-desktop.png"), fullPage: true });
        await page.getByRole("main").getByRole("link", { name: "Return to dashboard" }).click();
        await expect(page).toHaveURL(/\/dashboard\/$/);
        await page.getByRole("link", { name: "Demo walkthrough", exact: true }).click();
        await expect(page).toHaveURL(/\/walkthrough\/$/);
        await expect(page.getByRole("main").getByRole("link", { name: "Return to dashboard" })).toBeVisible();
        await page.screenshot({ path: testInfo.outputPath("guide-desktop.png"), fullPage: true });
    });
});
