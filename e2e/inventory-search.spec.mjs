import { sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

const stockItem = "SPR-B003-STD @ SYD-DC";
const statusFields = {
  product_active: "Product active",
  warehouse_active: "Warehouse active",
  supplier_active: "Supplier active",
  supplier_approved: "Supplier approved",
};

for (const account of ["supervisor", "clerk"]) {
  test.describe(`inventory search as ${account}`, () => {
    test.use({ storageState: sessionFor(account) });

    test("finds the walkthrough item and filters by its eligibility checks", async ({
      page,
    }) => {
      await page.goto("/catalog/inventoryrecord/list/");
      await page.getByRole("searchbox").fill(stockItem);
      const searched = page.waitForResponse((response) => {
        const url = new URL(response.url());
        return (
          url.pathname === "/routes/catalog/inventoryrecord/" &&
          url.searchParams.get("s") === stockItem
        );
      });
      await page.getByRole("button", { name: "Search", exact: true }).click();
      const response = await searched;
      expect(response.status()).toBe(200);
      const body = await response.json();
      expect(body.totalRecords).toBe(1);
      expect(body.results[0].formatted_name).toBe(stockItem);
      const row = page.getByRole("row").filter({ hasText: stockItem });
      await expect(row).toBeVisible();
      await expect(row.getByText("Yes", { exact: true })).toHaveCount(4);

      for (const [field, label] of Object.entries(statusFields)) {
        expect(body.results[0][field]).toBe(true);
        await expect(
          page.getByRole("columnheader", { name: label, exact: true }),
        ).toBeVisible();
        await page
          .getByRole("button", { name: "Filters", exact: true })
          .click();
        await page.getByRole("button", { name: label, exact: true }).click();
        const menu = page.locator('[data-qa="filter-menu-content"]');
        await menu.getByRole("combobox").click();
        await page.getByRole("option", { name: "Yes", exact: true }).click();
        const filtered = page.waitForResponse((response) => {
          const url = new URL(response.url());
          return (
            url.pathname === "/routes/catalog/inventoryrecord/" &&
            url.searchParams.get(field) === "true"
          );
        });
        await menu.getByRole("button", { name: "Apply", exact: true }).click();
        const filteredResponse = await filtered;
        expect(filteredResponse.status()).toBe(200);
        expect((await filteredResponse.json()).totalRecords).toBe(1);
      }

      await page.getByRole("searchbox").fill("nonexistent-stock-item");
      const empty = page.waitForResponse((response) => {
        const url = new URL(response.url());
        return (
          url.pathname === "/routes/catalog/inventoryrecord/" &&
          url.searchParams.get("s") === "nonexistent-stock-item"
        );
      });
      await page.getByRole("button", { name: "Search", exact: true }).click();
      expect((await (await empty).json()).totalRecords).toBe(0);
      await expect(row).toHaveCount(0);
    });
  });
}
