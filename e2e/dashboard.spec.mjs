/**
 * The dashboard's value tile asks for the total it shows.
 *
 * Column totals are opt-in: a list request that names none gets an empty `columnTotals`,
 * and the tile would quietly render 0.00. This pins the request and the number together.
 */
import { sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

test.use({ storageState: sessionFor("accountant") });

test("the open order value tile requests and shows a real total", async ({ page }) => {
    const totalled = page.waitForResponse((response) => {
        const url = new URL(response.url());
        return url.pathname === "/routes/catalog/purchaseorder/" && url.searchParams.get("ct") === "total_value";
    });

    await page.goto("/dashboard/");

    const body = await (await totalled).json();
    expect(body.columnTotals.total_value).toBeGreaterThan(0);
    await expect(page.getByText("Open order value")).toBeVisible();
});
