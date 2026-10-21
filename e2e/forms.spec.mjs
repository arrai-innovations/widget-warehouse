import { apiGet, orderId, sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

test.use({ storageState: sessionFor("supervisor") });

test("the sectioned purchase order form saves its reference without losing its lines", async ({ page }) => {
    const id = await orderId(page, "PO-1043");
    const path = `/routes/catalog/purchaseorder/${id}/`;
    const before = await apiGet(page, `${path}?e=lines`);
    expect(before.lines.length).toBeGreaterThan(0);

    await page.goto(`/catalog/purchaseorder/update/${id}`);
    await page.getByRole("textbox", { name: "Reference", exact: true }).fill("PO-1043-UPDATED");
    const saved = page.waitForResponse(
        (response) =>
            new URL(response.url()).pathname === path &&
            ["PUT", "PATCH"].includes(response.request().method()) &&
            !response.request().headers()["dry-run"],
    );
    await page.getByRole("button", { name: "Update", exact: true }).click();
    expect((await saved).status()).toBe(200);

    const after = await apiGet(page, `${path}?e=lines`);
    expect(after.reference).toBe("PO-1043-UPDATED");
    expect(after.lines).toEqual(before.lines);
});

test("replenishment accepts a selection carried as repeated pk query values", async ({ page }) => {
    const inventory = await apiGet(page, "/routes/catalog/inventoryrecord/?f=id");
    const selected = inventory.results.slice(0, 2).map((record) => String(record.id));
    expect(selected).toHaveLength(2);
    const query = new URLSearchParams(selected.map((id) => ["pk", id]));
    const preview = page.waitForResponse(
        (response) => new URL(response.url()).pathname === "/routes/catalog/inventoryrecord/replenish/",
    );

    await page.goto(`/catalog/inventoryrecord/replenish/?${query}`);

    const response = await preview;
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.rows.map((row) => String(row.inventory_id)).sort()).toEqual([...selected].sort());
});
