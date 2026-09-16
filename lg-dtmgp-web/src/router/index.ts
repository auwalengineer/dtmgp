import { createRouter, createWebHistory } from "vue-router";

import ModulePlaceholder from "@/views/ModulePlaceholder.vue";
import OverviewView from "@/views/OverviewView.vue";
import PeopleHrView from "@/views/PeopleHrView.vue";
import LoginView from "@/views/LoginView.vue";
import UsersView from "@/views/UsersView.vue";
import AdministrationView from "@/views/AdministrationView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "overview", component: OverviewView, meta: { title: "Overview" } },
    { path: "/people", name: "people", component: PeopleHrView, meta: { title: "People & HR" } },
    { path: "/administration", name: "administration", component: AdministrationView, meta: { title: "Administration", requiresUserAdmin: true } },
    { path: "/administration/users", name: "users", component: UsersView, meta: { title: "Users", requiresUserAdmin: true } },
    {
      path: "/:module(people|finance|projects|traditional-affairs|analytics)",
      name: "module",
      component: ModulePlaceholder,
    },
  ],
});
