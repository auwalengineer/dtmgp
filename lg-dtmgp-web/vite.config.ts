import { fileURLToPath, URL } from "node:url";
import { readFileSync } from "node:fs";

import vue from "@vitejs/plugin-vue";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const backendOrigin = env.VITE_BACKEND_ORIGIN || "http://blga.local:8000";
  let buildCommit = process.env.GITHUB_SHA || "development";
  try { buildCommit = JSON.parse(readFileSync("public/version.json", "utf8")).commit || buildCommit; } catch { /* use fallback */ }

  return {
    plugins: [vue()],
    define: { __BUILD_VERSION__: JSON.stringify(buildCommit) },
    resolve: {
      alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": { target: backendOrigin, changeOrigin: true },
        "/assets": { target: backendOrigin, changeOrigin: true },
        // Employee photos and other attachments are served by Frappe (private ones are session-checked).
        "/files": { target: backendOrigin, changeOrigin: true },
        "/private": { target: backendOrigin, changeOrigin: true },
      },
    },
    preview: { host: "0.0.0.0", port: 4173 },
    build: { sourcemap: mode !== "production" },
  };
});
