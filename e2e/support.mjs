/**
 * What the specs share: where the two servers are, the demo accounts, and helpers for
 * reading the requests a page sends.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";

const serverPort = process.env.E2E_SERVER_PORT || "8100";
const clientPort = process.env.E2E_CLIENT_PORT || "8180";

export const SERVER_PORT = serverPort;
export const CLIENT_PORT = clientPort;
export const SERVER_ORIGIN = `http://localhost:${serverPort}`;
export const CLIENT_ORIGIN = `http://localhost:${clientPort}`;

// The published demo accounts, as ViewSignIn lists them. Not secrets.
export const DEMO_PASSWORD = "widget-demo";
export const ACCOUNTS = {
    clerk: "clerk@widgetwarehouse.com",
    supervisor: "supervisor@widgetwarehouse.com",
    accountant: "accountant@widgetwarehouse.com",
};

const AUTH_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), ".auth");

/** The saved session for one demo account, written by auth.setup.mjs. */
export function sessionFor(account) {
    return path.join(AUTH_DIR, `${account}.json`);
}

/**
 * Record every request the page sends to the API server from now on.
 *
 * @param {import('@playwright/test').Page} page
 * @returns {URL[]} Filled in as requests go out.
 */
export function recordApiRequests(page) {
    const requests = [];
    page.on("request", (request) => {
        const url = new URL(request.url());
        if (url.origin === SERVER_ORIGIN) {
            requests.push(url);
        }
    });
    return requests;
}

/**
 * Read one API path with the page's session, as the client would.
 *
 * @param {import('@playwright/test').Page} page
 * @param {string} apiPath - Path under the API origin, with any query.
 */
export async function apiGet(page, apiPath) {
    const response = await page.request.get(`${SERVER_ORIGIN}${apiPath}`);
    if (!response.ok()) {
        throw new Error(`GET ${apiPath} returned ${response.status()}: ${await response.text()}`);
    }
    return response.json();
}

/** The id of a seeded purchase order, looked up by its reference. */
export async function orderId(page, reference) {
    const page_ = await apiGet(page, `/routes/catalog/purchaseorder/?reference=${encodeURIComponent(reference)}`);
    const match = page_.results.find((row) => row.reference === reference);
    if (!match) {
        throw new Error(`No purchase order ${reference} in the seeded data`);
    }
    return match.id;
}
