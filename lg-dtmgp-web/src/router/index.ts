import { createRouter, createWebHistory } from "vue-router";

import ModulePlaceholder from "@/views/ModulePlaceholder.vue";
import OverviewView from "@/views/OverviewView.vue";
import PeopleHrView from "@/views/PeopleHrView.vue";
import LoginView from "@/views/LoginView.vue";
import UsersView from "@/views/UsersView.vue";
import AdministrationView from "@/views/AdministrationView.vue";
import SystemWorkspaceView from "@/views/SystemWorkspaceView.vue";
import WorkspaceView from "@/views/WorkspaceView.vue";
import FinanceView from "@/views/FinanceView.vue";
import FinanceWorkspaceView from "@/views/FinanceWorkspaceView.vue";
import GovernanceView from "@/views/GovernanceView.vue";
import ProjectsView from "@/views/ProjectsView.vue";
import TraditionalAffairsView from "@/views/TraditionalAffairsView.vue";
import AnalyticsView from "@/views/AnalyticsView.vue";
import MyProfileView from "@/views/global/MyProfileView.vue";
import MyTasksView from "@/views/global/MyTasksView.vue";
import MyApprovalsView from "@/views/global/MyApprovalsView.vue";
import RecentlyViewedView from "@/views/global/RecentlyViewedView.vue";
import HelpSupportView from "@/views/global/HelpSupportView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/login", name: "login", component: LoginView, meta: { public: true } },
    { path: "/", name: "overview", component: OverviewView, meta: { title: "Overview" } },
    { path: "/people", name: "people", component: PeopleHrView, meta: { title: "People & HR", requiresHrAccess: true } },
    { path: "/finance", name: "finance", component: FinanceView, meta: { title: "Finance, Revenue & Procurement", requiresFinanceAccess: true } },
    { path: "/governance", name: "governance", component: GovernanceView, meta: { title: "Administration & Governance", requiresGovernanceAccess: true } },
    { path: "/traditional-affairs", name: "traditional-affairs", component: TraditionalAffairsView, meta: { title: "Chieftaincy & Traditional Institutions", requiresTraditionalAccess: true } },
    { path: "/projects", name: "projects", component: ProjectsView, meta: { title: "Projects, Assets & Field Monitoring", requiresProjectsAccess: true } },
    { path: "/analytics", name: "analytics", component: AnalyticsView, meta: { title: "Executive Dashboard & Analytics", requiresAnalyticsAccess: true } },
    { path: "/administration", name: "administration", component: AdministrationView, meta: { title: "Administration", requiresUserAdmin: true } },
    { path: "/administration/users", name: "users", component: UsersView, meta: { title: "Users", requiresUserAdmin: true } },
    { path: "/workspace/system/:section/:item?", name: "system-workspace", component: SystemWorkspaceView, meta: { title: "System Administration", requiresUserAdmin: true } },
    { path: "/workspace/hr/:section/:item?", name: "hr-workspace", component: PeopleHrView, meta: { title: "People & HR", requiresHrAccess: true } },
    { path: "/workspace/governance/:section/:item?", name: "governance-workspace", component: GovernanceView, meta: { title: "Administration & Governance", requiresGovernanceAccess: true } },
    { path: "/workspace/traditional/:section/:item?", name: "traditional-workspace", component: TraditionalAffairsView, meta: { title: "Chieftaincy & Traditional Institutions", requiresTraditionalAccess: true } },
    { path: "/workspace/finance/:section/:item?", name: "finance-workspace", component: FinanceWorkspaceView, meta: { title: "Finance, Revenue & Procurement", requiresFinanceAccess: true } },
    { path: "/workspace/projects/:section/:item?", name: "projects-workspace", component: ProjectsView, meta: { title: "Projects, Assets & Field Monitoring", requiresProjectsAccess: true } },
    { path: "/workspace/analytics/:section/:item?", name: "analytics-workspace", component: AnalyticsView, meta: { title: "Executive Dashboard & Analytics", requiresAnalyticsAccess: true } },
    { path: "/workspace/global/my-tasks", name: "my-tasks", component: MyTasksView, meta: { title: "My Tasks" } },
    { path: "/workspace/global/my-approvals", name: "my-approvals", component: MyApprovalsView, meta: { title: "My Approvals" } },
    { path: "/workspace/global/recently-viewed", name: "recently-viewed", component: RecentlyViewedView, meta: { title: "Recently Viewed" } },
    { path: "/workspace/global/help-support", name: "help-support", component: HelpSupportView, meta: { title: "Help & Support" } },
    { path: "/workspace/global/my-profile", name: "my-profile", component: MyProfileView, meta: { title: "My Profile" } },
    { path: "/workspace/:domain/:section?/:item?", name: "workspace", component: WorkspaceView },
    {
      path: "/:module(people)",
      name: "module",
      component: ModulePlaceholder,
      meta: { requiresNavigationModule: true },
    },
  ],
});
