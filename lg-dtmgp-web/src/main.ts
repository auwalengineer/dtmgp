import { VueQueryPlugin } from "@tanstack/vue-query";
import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import { loadEnvironment } from "./config/environment";
import { router } from "./router";
import "./styles/main.css";

async function bootstrap() {
  const environment = await loadEnvironment();
  const app = createApp(App);

  app.provide("environment", environment);
  app.use(createPinia());
  app.use(VueQueryPlugin);
  app.use(router);
  app.mount("#app");
}

void bootstrap();
