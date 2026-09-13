import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  const backendOrigin = env.VITE_BACKEND_ORIGIN || "http://blga.local:8000";

  return {
    plugins: [vue()],
    resolve: {
      alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": { target: backendOrigin, changeOrigin: true },
        "/assets": { target: backendOrigin, changeOrigin: true },
      },
    },
    preview: { host: "0.0.0.0", port: 4173 },
    build: { sourcemap: mode !== "production" },
  };
});
