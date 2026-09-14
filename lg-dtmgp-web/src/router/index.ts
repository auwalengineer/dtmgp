import { createRouter, createWebHistory } from "vue-router";

import ModulePlaceholder from "@/views/ModulePlaceholder.vue";
import OverviewView from "@/views/OverviewView.vue";
import PeopleHrView from "@/views/PeopleHrView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "overview", component: OverviewView, meta: { title: "Overview" } },
    { path: "/people", name: "people", component: PeopleHrView, meta: { title: "People & HR" } },
    {
      path: "/:module(administration|people|finance|projects|traditional-affairs|analytics)",
      name: "module",
      component: ModulePlaceholder,
    },
  ],
});
