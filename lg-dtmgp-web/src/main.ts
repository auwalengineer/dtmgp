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
  const session = useSessionStore(pinia);
  await session.restore();
  router.beforeEach((to) => {
    if (to.meta.public && session.authenticated) return "/";
    if (!to.meta.public && !session.authenticated) return { name: "login", query: { redirect: to.fullPath } };
    if (to.meta.requiresUserAdmin && !session.canManageUsers) return { name: "overview" };
    if (to.meta.requiresHrAccess && !session.canViewHr) return { name: "overview" };
    if (to.meta.requiresGovernanceAccess && !session.canViewGovernance) return { name: "overview" };
    if (to.meta.requiresTraditionalAccess && !session.navigation.some((module) => module.id === "traditional")) return { name: "overview" };
    if (to.meta.requiresFinanceAccess && !session.canViewFinance) return { name: "overview" };
    if (to.meta.requiresProjectsAccess && !session.canViewProjects) return { name: "overview" };
    if (to.meta.requiresAnalyticsAccess && !session.canViewAnalytics) return { name: "overview" };
    if (to.name === "workspace") {
      const routes = session.navigation.flatMap(module => module.children.flatMap(section => [section.to, ...(section.children || []).map(item => item.to)]));
      if (![...routes, ...session.globalMenu.map(item => item.to)].includes(to.path)) return { name: "overview" };
    }
    if (to.meta.requiresNavigationModule) {
      const domain = String(to.params.module).replace("traditional-affairs", "traditional");
      if (!session.navigation.some(module => module.id === domain)) return { name: "overview" };
    }
  });
  app.use(router);
  await router.isReady();
  app.mount("#app");
}

void bootstrap();
