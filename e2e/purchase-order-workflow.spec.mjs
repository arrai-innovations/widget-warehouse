/**
 * The purchase order workflow, driven through the browser: a transition route, the
 * transition itself, and the state permission that takes update away from the clerk.
 *
 * Workflow state history has no spec here. Widget Warehouse does not mount VUEDA's
 * history routes, and nothing in its client reads state history.
 */
import { apiGet, orderId, sessionFor } from "./support.mjs";
import { expect, test } from "@playwright/test";

// A draft in the seed that no other spec touches.
const REFERENCE = "PO-1044";

async function availableActions(page, id) {
    return (await apiGet(page, `/routes/catalog/purchaseorder/${id}/?f=available_actions`)).available_actions;
}

test("submitting a draft takes update away from the clerk but not the supervisor", async ({ browser }) => {
    const clerk = await browser.newContext({ storageState: sessionFor("clerk") });
    const supervisor = await browser.newContext({ storageState: sessionFor("supervisor") });
    const clerkPage = await clerk.newPage();
    const supervisorPage = await supervisor.newPage();
    const id = await orderId(clerkPage, REFERENCE);

    expect(await availableActions(clerkPage, id)).toContain("update");

    // The form dry-runs the transition when it loads. The confirm button sends the real
    // request, without the Dry-Run header, which is the one that moves the order.
    const executed = clerkPage.waitForResponse(
        (response) =>
            new URL(response.url()).pathname.includes("/workflows/catalog/purchaseorder/execute-transition/") &&
            response.request().method() === "PATCH" &&
            !response.request().headers()["dry-run"],
    );
    await clerkPage.goto(`/catalog/purchaseorder/submit/${id}`);
    await clerkPage.getByRole("button", { name: "Yes, continue" }).click();
    expect((await executed).status()).toBe(200);

    const state = await apiGet(clerkPage, `/routes/catalog/purchaseorder/${id}/?f=workflow_state_code`);
    expect(state.workflow_state_code).toBe("submitted");
    expect(await availableActions(clerkPage, id)).not.toContain("update");
    expect(await availableActions(supervisorPage, id)).toContain("update");

    await clerk.close();
    await supervisor.close();
});
