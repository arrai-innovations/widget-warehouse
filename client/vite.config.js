import { vuedaViteConfig } from "@arrai-innovations/vueda/lib/vite.js";
import tailwindcss from "@tailwindcss/vite";
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
        enableRuntimeAliases: false,
        extraAliases: {
            "@": path.resolve(__dirname, "src"),
        },
    });

    return {
        plugins: [vue(), tailwindcss()],
        ...vueda,
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
