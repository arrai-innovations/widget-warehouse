/**
 * End-to-end tests: the built client against the real server, in a browser.
 *
 * `just test-e2e` starts both servers itself, on ports of their own, against a database
 * of its own (see e2e/serve.py), and stops them afterwards. Nothing a developer runs
 * locally is reused or touched, so the servers are never shared with a dev session.
 *
 * These cover what neither package's unit tests can: the client and the server meeting
 * over the wire. Each spec asserts on the requests the browser sends and the answers it
 * gets, rather than on markup.
 */
import { CLIENT_ORIGIN, CLIENT_PORT, SERVER_ORIGIN, SERVER_PORT } from "./e2e/support.mjs";
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
    testDir: "e2e",
    outputDir: "e2e/test-results",
    // Every spec shares one seeded database, and some specs change it. One worker keeps
    // the order they run in the order they are written.
    workers: 1,
    fullyParallel: false,
    forbidOnly: Boolean(process.env.CI),
    reporter: [["list"], ["html", { outputFolder: "e2e/playwright-report", open: "never" }]],
    use: {
        baseURL: CLIENT_ORIGIN,
        trace: "retain-on-failure",
    },
    projects: [
        { name: "setup", testMatch: /auth\.setup\.mjs/ },
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] },
            dependencies: ["setup"],
        },
    ],
    webServer: [
        {
            // Migrates, resets the demo, then serves, so every run starts from the seed.
            command: "uv run --no-sync python ../e2e/serve.py",
            cwd: "server",
            url: `${SERVER_ORIGIN}/routes/vueda.user/who-is/`,
            env: { E2E_SERVER_PORT: SERVER_PORT, E2E_CLIENT_PORT: CLIENT_PORT },
            reuseExistingServer: false,
            timeout: 180_000,
            stdout: "pipe",
        },
        {
            command: `pnpm exec vite --mode e2e --port ${CLIENT_PORT} --strictPort`,
            cwd: "client",
            url: CLIENT_ORIGIN,
            env: { VITE_DJANGO_CONNECTION_PORT: SERVER_PORT },
            reuseExistingServer: false,
            timeout: 120_000,
        },
    ],
});
