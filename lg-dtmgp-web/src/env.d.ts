/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_ENV: "development" | "staging" | "production";
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_BACKEND_ORIGIN?: string;
  readonly VITE_RUNTIME_CONFIG_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
