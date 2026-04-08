import { vuedaViteConfig } from "@arrai-innovations/vueda/lib/vite.js";
import vue from "@vitejs/plugin-vue";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { defineConfig, loadEnv } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");

    let https;
    if (env.HTTPS_KEY_PATH && fs.existsSync(env.HTTPS_KEY_PATH)) {
        https = {
            key: fs.readFileSync(env.HTTPS_KEY_PATH),
            cert: fs.readFileSync(env.HTTPS_CERT_PATH),
        };
    }

    const hmrHost = env.HMR_HOST;
    const hmrPort = Number(env.HMR_PORT || 8080);
    const hmrProtocol = env.HMR_PROTOCOL || (https ? "wss" : "ws");

    const vueda = vuedaViteConfig({
        extraAliases: {
            "@": path.resolve(__dirname, "src"),
        },
        optimizeDeps: {
            exclude: ["@arrai-innovations/vueda"],
            include: [
                "@arrai-innovations/reactive-helpers",
                "@sentry/vue",
                "@vueuse/core",
                "@vueuse/shared",
                "lodash-es",
                "vue",
                "vue-router",
            ],
        },
    });

    return {
        plugins: [vue()],
        define: vueda.define,
        resolve: {
            ...vueda.resolve,
            // Force shared packages to resolve from this project's
            // node_modules, preventing duplicate instances when vueda
            // is linked locally via link: protocol.
            dedupe: [
                "vue",
                "vue-router",
                "pinia",
                "primevue",
                "@primeuix/themes",
                "@primeuix/styled",
                "@vueuse/core",
                "@vueuse/shared",
                "@floating-ui/vue",
                "@floating-ui/dom",
                "lodash-es",
                "luxon",
            ],
        },
        optimizeDeps: vueda.optimizeDeps,
        server: {
            host: true,
            port: 8080,
            strictPort: true,
            https,
            hmr: hmrHost
                ? {
                      host: hmrHost,
                      port: hmrPort,
                      protocol: hmrProtocol,
                  }
                : true,
        },
        preview: {
            host: true,
            port: 8080,
            strictPort: true,
            https,
        },
    };
});
