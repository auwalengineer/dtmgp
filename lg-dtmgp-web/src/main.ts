import { VueQueryPlugin } from "@tanstack/vue-query";
import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { loadEnvironment } from "./config/environment";
import { router } from "./router";
import { useSessionStore } from "./stores/session";
import "./styles/main.css";

async function bootstrap() {
  const environment = await loadEnvironment();
  const app = createApp(App);
  const pinia = createPinia();

  app.provide("environment", environment);
  app.use(pinia);
  app.use(VueQueryPlugin);
  app.use(router);
  const session = useSessionStore(pinia);
  await session.restore();
  router.beforeEach((to) => {
    if (to.meta.public && session.authenticated) return "/";
    if (!to.meta.public && !session.authenticated) return { name: "login", query: { redirect: to.fullPath } };
    if (to.meta.requiresUserAdmin && !session.canManageUsers) return { name: "overview" };
  });
  await router.isReady();
  app.mount("#app");
}

void bootstrap();
