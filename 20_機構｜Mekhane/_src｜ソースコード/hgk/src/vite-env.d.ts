/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_BASE: string
    // more env variables...
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}

// Tauri IPC environment detection
interface Window {
    __TAURI_INTERNALS__?: Record<string, unknown>;
}
