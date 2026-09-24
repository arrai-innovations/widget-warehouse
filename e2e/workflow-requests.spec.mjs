/**
 * The client asks the workflow API only about models that report workflow.
 *
 * Model info carries `workflow_enabled`, and VUEDA's workflow store reads it before any
 * workflow request. A purchase order is the demo's one workflow model; widgets and
 * inventory records are ordinary models and must cost no workflow request at all.
 */
import { recordApiRequests, sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

const isWorkflowRequest = (url) => url.pathname.startsWith("/routes/vueda.workflow/");

test.describe("as the supervisor", () => {
    test.use({ storageState: sessionFor("supervisor") });

    for (const model of ["widget", "inventoryrecord"]) {
        test(`the ${model} list sends no workflow request`, async ({ page }) => {
            const requests = recordApiRequests(page);
            const list = page.waitForResponse((response) =>
                new URL(response.url()).pathname.startsWith(`/routes/catalog/${model}/`),
            );

            await page.goto(`/catalog/${model}/list/`);
            expect((await list).status()).toBe(200);
            await page.waitForLoadState("networkidle");

            expect(requests.filter(isWorkflowRequest).map((url) => url.pathname)).toEqual([]);
        });
    }

    test("the purchase order list asks for the order's transitions", async ({ page }) => {
        const transitions = page.waitForResponse((response) =>
            new URL(response.url()).pathname.endsWith("/workflows/catalog/purchaseorder/permitted_transitions/"),
        );

        await page.goto("/catalog/purchaseorder/list/");

        expect((await transitions).status()).toBe(200);
    });
});
