/**
 * The purchase order's delivery is an optional reverse one-to-one, edited as a singular
 * inline. These specs cover the create form: the empty row the inline starts with, the
 * request a save sends for it, and what the server stores.
 */
import fs from "node:fs";

import { apiGet, sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

test.use({ storageState: sessionFor("supervisor") });

const ORDER_PATH = "/routes/catalog/purchaseorder/";

function fieldSet(page, title) {
    return page.locator("[data-vueda-fieldset]").filter({ has: page.getByRole("button", { name: title, exact: true }) });
}

async function openCreate(page) {
    await page.goto("/catalog/purchaseorder/create");
    await page.getByRole("textbox", { name: "Reference", exact: true }).waitFor();
    await expect(page.getByRole("textbox", { name: "Carrier" })).toBeVisible();
}

async function pickFirstOption(page, placeholder) {
    await page.getByRole("button", { name: "Show popup" }).filter({ hasText: placeholder }).click();
    await page.getByRole("option").first().click();
}

/** Fill every required order field and one line, leaving the delivery alone. */
async function fillOrder(page, reference) {
    await page.getByRole("textbox", { name: "Reference", exact: true }).fill(reference);
    await pickFirstOption(page, "Select a supplier");
    await pickFirstOption(page, "Select a warehouse");
    // The first date field on the form is Order Date; Expected Arrival Date follows it.
    await page.getByRole("spinbutton", { name: "month," }).first().click();
    await page.keyboard.type("11092026");

    const lines = fieldSet(page, "Lines");
    await lines.getByRole("button", { name: "Create", exact: true }).click();
    const row = lines.getByRole("row").nth(1);
    await row.getByRole("button", { name: "Show popup" }).click();
    await page.getByRole("option").first().click();
    const numbers = row.getByRole("spinbutton");
    await numbers.nth(0).fill("1");
    await numbers.nth(1).fill("1");
}

/**
 * Submit the create form. Returns the write request and its response, or the client
 * validation messages when the form sends nothing.
 */
async function submitCreate(page) {
    const request = page
        .waitForRequest(
            (req) =>
                new URL(req.url()).pathname === ORDER_PATH && req.method() === "POST" && !req.headers()["dry-run"],
            { timeout: 8000 },
        )
        .catch(() => null);
    await page.getByRole("button", { name: "Create", exact: true }).first().click();
    const sent = await request;
    if (!sent) {
        return { sent: false, clientErrors: await page.getByRole("alert").allTextContents() };
    }
    const response = await sent.response();
    return {
        sent: true,
        expand: new URL(sent.url()).searchParams.get("e") ?? "",
        body: sent.postDataJSON(),
        status: response?.status(),
        responseBody: await response?.json().catch(() => null),
    };
}

async function savedDelivery(page, reference) {
    const list = await apiGet(page, `${ORDER_PATH}?reference=${encodeURIComponent(reference)}&e=delivery&f=id,reference,delivery`);
    const order = list.results.find((row) => row.reference === reference);
    return order ? { orderId: order.id, delivery: order.delivery ?? null } : null;
}

function record(testInfo, name, data) {
    fs.writeFileSync(testInfo.outputPath(`${name}.json`), JSON.stringify(data, null, 2));
}

test("an optional delivery starts as an empty unsaved row with a Delete button", async ({ page }, testInfo) => {
    await openCreate(page);
    const section = fieldSet(page, "Delivery");
    await expect(section.getByRole("button", { name: "Delete", exact: true })).toBeVisible();
    await expect(section.getByRole("button", { name: "Delete on save" })).toHaveCount(0);
    await expect(section.getByRole("checkbox")).toHaveCount(0);
    await page.screenshot({ path: testInfo.outputPath("optional-empty-row.png"), fullPage: true });
});

test("deleting the unsaved delivery clears it, and the order saves without one", async ({ page }, testInfo) => {
    await openCreate(page);
    const section = fieldSet(page, "Delivery");
    await section.getByRole("button", { name: "Delete", exact: true }).click();
    await expect(page.getByRole("textbox", { name: "Carrier" })).toHaveCount(0);
    await expect(section.getByRole("button", { name: "Create", exact: true })).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath("optional-cleared.png"), fullPage: true });

    await fillOrder(page, "PO-E2E-CLEARED");
    const result = await submitCreate(page);
    const stored = await savedDelivery(page, "PO-E2E-CLEARED");
    record(testInfo, "cleared", { ...result, stored });

    expect(result.sent).toBe(true);
    expect(result.expand.split(",")).not.toContain("delivery");
    expect(result.status).toBe(201);
    expect(stored?.delivery).toBeNull();
});

test("saving with the untouched empty delivery row", async ({ page }, testInfo) => {
    await openCreate(page);
    await fillOrder(page, "PO-E2E-UNTOUCHED");
    const result = await submitCreate(page);
    const stored = await savedDelivery(page, "PO-E2E-UNTOUCHED");
    record(testInfo, "untouched", { ...result, stored });
    await page.screenshot({ path: testInfo.outputPath("untouched-after-save.png"), fullPage: true });
});

test("probe: untouched empty row when no child field is required", async ({ page }, testInfo) => {
    await page.route(
        (url) => url.pathname === "/routes/vueda.info/model_info/catalog/purchaseorder/",
        async (route) => {
            const response = await route.fetch();
            const json = await response.json();
            const expands = json.model_expands;
            const entries = Array.isArray(expands) ? expands : Object.values(expands ?? {});
            for (const entry of entries) {
                if (entry?.name === "delivery" && entry.f?.carrier) {
                    entry.f.carrier.required = false;
                }
            }
            await route.fulfill({ response, json });
        },
    );
    await openCreate(page);
    await fillOrder(page, "PO-E2E-UNTOUCHED-OPTIONAL");
    const result = await submitCreate(page);
    const stored = await savedDelivery(page, "PO-E2E-UNTOUCHED-OPTIONAL");
    record(testInfo, "untouched-optional-child", { ...result, stored });
});

test("a filled-in delivery saves with the new order", async ({ page }, testInfo) => {
    await openCreate(page);
    await fillOrder(page, "PO-E2E-FILLED");
    await page.getByRole("textbox", { name: "Carrier" }).fill("StarTrack");
    const result = await submitCreate(page);
    const stored = await savedDelivery(page, "PO-E2E-FILLED");
    record(testInfo, "filled", { ...result, stored });

    expect(result.sent).toBe(true);
    expect(result.expand.split(",")).toContain("delivery");
    expect(result.status).toBe(201);
    expect(stored?.delivery?.carrier).toBe("StarTrack");
});

test("a required delivery offers no Delete button on its auto-created row", async ({ page }, testInfo) => {
    // Mark the relation required in model info, as a serializer with required=True would.
    await page.route(
        (url) => url.pathname === "/routes/vueda.info/model_info/catalog/purchaseorder/",
        async (route) => {
            const response = await route.fetch();
            const json = await response.json();
            if (json.model_fields?.delivery) {
                json.model_fields.delivery.required = true;
            }
            const expands = json.model_expands;
            const entries = Array.isArray(expands) ? expands : Object.values(expands ?? {});
            for (const entry of entries) {
                if (entry?.name === "delivery") {
                    entry.required = true;
                }
            }
            await route.fulfill({ response, json });
        },
    );
    await openCreate(page);
    const section = fieldSet(page, "Delivery");
    await expect(page.getByRole("textbox", { name: "Carrier" })).toBeVisible();
    await expect(section.getByRole("button", { name: "Delete", exact: true })).toHaveCount(0);
    await expect(section.getByRole("button", { name: "Delete on save" })).toHaveCount(0);
    await page.screenshot({ path: testInfo.outputPath("required-row.png"), fullPage: true });
});
