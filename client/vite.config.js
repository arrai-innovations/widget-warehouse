import { vuedaViteConfig } from "@arrai-innovations/vueda/lib/vite.js";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { defineConfig, loadEnv } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Read rather than imported: this config is ESM, where a JSON import needs an import
// attribute, and the same read is how the vueda client's own version is picked up.
const packageDetails = JSON.parse(fs.readFileSync(path.resolve(__dirname, "package.json"), "utf-8"));

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "");

    // The client's own version, which VUEDA reads back as `projectClientVersion` and compares
    // against the deployed one. It comes off disk so a dev build reports a real version too;
    // taking it from the release tag left it undefined everywhere except a tagged CI build.
    // client.yml checks this against the tag it is releasing.
    process.env.VITE_PACKAGE_NAME = packageDetails.name;
    process.env.VITE_PACKAGE_VERSION = packageDetails.version;

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
            // Preserve vuedaViteConfig's server config (notably fs.allow for linked vueda source);
            // the app's own keys below still take precedence.
            ...vueda.server,
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
