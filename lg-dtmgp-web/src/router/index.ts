import { createRouter, createWebHistory } from "vue-router";

import ModulePlaceholder from "@/views/ModulePlaceholder.vue";
import OverviewView from "@/views/OverviewView.vue";
import PeopleHrView from "@/views/PeopleHrView.vue";
import LoginView from "@/views/LoginView.vue";
import UsersView from "@/views/UsersView.vue";
import AdministrationView from "@/views/AdministrationView.vue";
import WorkspaceView from "@/views/WorkspaceView.vue";
import FinanceView from "@/views/FinanceView.vue";
import FinanceWorkspaceView from "@/views/FinanceWorkspaceView.vue";
import GovernanceView from "@/views/GovernanceView.vue";
import TraditionalAffairsView from "@/views/TraditionalAffairsView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "overview", component: OverviewView, meta: { title: "Overview" } },
    { path: "/people", name: "people", component: PeopleHrView, meta: { title: "People & HR", requiresHrAccess: true } },
    { path: "/finance", name: "finance", component: FinanceView, meta: { title: "Finance, Revenue & Procurement", requiresFinanceAccess: true } },
    { path: "/governance", name: "governance", component: GovernanceView, meta: { title: "Administration & Governance", requiresGovernanceAccess: true } },
    { path: "/traditional-affairs", name: "traditional-affairs", component: TraditionalAffairsView, meta: { title: "Chieftaincy & Traditional Institutions", requiresTraditionalAccess: true } },
    { path: "/administration", name: "administration", component: AdministrationView, meta: { title: "Administration", requiresUserAdmin: true } },
    { path: "/administration/users", name: "users", component: UsersView, meta: { title: "Users", requiresUserAdmin: true } },
    { path: "/workspace/hr/:section/:item?", name: "hr-workspace", component: PeopleHrView, meta: { title: "People & HR", requiresHrAccess: true } },
    { path: "/workspace/governance/:section/:item?", name: "governance-workspace", component: GovernanceView, meta: { title: "Administration & Governance", requiresGovernanceAccess: true } },
    { path: "/workspace/traditional/:section/:item?", name: "traditional-workspace", component: TraditionalAffairsView, meta: { title: "Chieftaincy & Traditional Institutions", requiresTraditionalAccess: true } },
    { path: "/workspace/finance/:section/:item?", name: "finance-workspace", component: FinanceWorkspaceView, meta: { title: "Finance, Revenue & Procurement", requiresFinanceAccess: true } },
    { path: "/workspace/:domain/:section?/:item?", name: "workspace", component: WorkspaceView },
    {
      path: "/:module(people|projects|analytics)",
      name: "module",
      component: ModulePlaceholder,
      meta: { requiresNavigationModule: true },
    },
  ],
});
