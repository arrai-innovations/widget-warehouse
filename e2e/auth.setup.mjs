/**
 * Sign each demo account in once, through the real sign-in page, and save its session.
 * The specs start from these sessions rather than signing in again.
 */
import { ACCOUNTS, DEMO_PASSWORD, sessionFor } from "./support.mjs";
import { expect, test as setup } from "@playwright/test";

for (const [account, email] of Object.entries(ACCOUNTS)) {
    setup(`sign in as ${account}`, async ({ page }) => {
        await page.goto("/sign-in/");
        await page.fill('input[autocomplete="username"]', email);
        await page.fill('input[autocomplete="current-password"]', DEMO_PASSWORD);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL(/\/dashboard\//);
        await page.context().storageState({ path: sessionFor(account) });
    });
}
