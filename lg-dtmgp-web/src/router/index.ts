import { createRouter, createWebHistory } from "vue-router";

import ModulePlaceholder from "@/views/ModulePlaceholder.vue";
import OverviewView from "@/views/OverviewView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "overview", component: OverviewView, meta: { title: "Overview" } },
    {
      path: "/:module(administration|people|finance|projects|traditional-affairs|analytics)",
      name: "module",
      component: ModulePlaceholder,
    },
  ],
});
