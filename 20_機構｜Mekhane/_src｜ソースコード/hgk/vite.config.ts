import { defineConfig } from "vite";

const host = process.env.TAURI_DEV_HOST;

// https://vitejs.dev/config/
export default defineConfig(async () => ({
    // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
    //
    // 1. prevent vite from obscuring rust errors
    clearScreen: false,
    // 2. tauri expects a fixed port, fail if that port is not available
    server: {
        port: 1420,
        strictPort: true,
        host: host || "0.0.0.0",
        hmr: host
            ? {
                protocol: "ws",
                host,
                port: 1421,
            }
            : undefined,
        proxy: {
            '/api': {
                target: process.env.HGK_BACKEND_URL || 'http://127.0.0.1:9696',
                changeOrigin: true,
            },
        },
        watch: {
            // Avoid inotify watchers entirely — Firefox ESR consumes 90K+ FDs,
            // leaving none for chokidar. Polling is slower but stable.
            usePolling: true,
            interval: 1000,
            ignored: [
                "**/src-tauri/**",
                "**/node_modules/**",
                "**/.git/**",
            ],
        },
    },
}));
