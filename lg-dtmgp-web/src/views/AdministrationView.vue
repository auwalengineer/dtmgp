<script setup lang="ts">
import { ArrowRight, Building2, Settings, ShieldCheck, UserRoundCheck, UserRoundX, UsersRound } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Dashboard {
  scope: string;
  lga_count: number;
  user_count: number;
  active_user_count: number;
  disabled_user_count: number;
  roles: { role: string; count: number }[];
  recent_users: { name: string; full_name: string; enabled: number; last_active: string | null }[];
}

const session = useSessionStore();
const dashboard = ref<Dashboard | null>(null);
const loading = ref(true);
const error = ref("");
const metrics = computed(() => dashboard.value ? [
  { label: "LGAs in scope", value: dashboard.value.lga_count, icon: Building2, tone: "green" },
  { label: "Managed users", value: dashboard.value.user_count, icon: UsersRound, tone: "blue" },
  { label: "Active users", value: dashboard.value.active_user_count, icon: UserRoundCheck, tone: "green" },
  { label: "Disabled users", value: dashboard.value.disabled_user_count, icon: UserRoundX, tone: "red" },
] : []);

async function loadDashboard() {
  loading.value = true;
  error.value = "";
  try {
    const company = session.activeLga ? `?company=${encodeURIComponent(session.activeLga)}` : "";
    dashboard.value = await apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.administration.get_dashboard${company}`);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load administration";
  } finally {
    loading.value = false;
  }
}

watch(() => session.activeLga, loadDashboard, { immediate: true });
</script>

<template>
  <section class="page-heading">
    <div><p class="eyebrow">Administration</p><h1>Access administration</h1><p>{{ dashboard?.scope || session.activeLga }}</p></div>
    <div style="display: flex; gap: 10px">
      <RouterLink class="secondary-action action-link" to="/workspace/system/user-management"><Settings :size="16" /> System Administration</RouterLink>
      <RouterLink class="primary-action action-link" to="/administration/users">Manage users <ArrowRight :size="17" /></RouterLink>
    </div>
  </section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading administration...</section>
  <template v-else-if="dashboard">
    <section class="admin-metrics">
      <article v-for="metric in metrics" :key="metric.label">
        <span class="admin-metric-icon" :class="metric.tone"><component :is="metric.icon" :size="20" /></span>
        <div><small>{{ metric.label }}</small><strong>{{ metric.value }}</strong></div>
      </article>
    </section>
    <div class="admin-grid">
      <section class="panel">
        <header class="panel-header"><div><h2>Recent accounts</h2><p>Newest users inside your current scope</p></div><RouterLink class="text-action" to="/administration/users">View all <ArrowRight :size="15" /></RouterLink></header>
        <div class="admin-user-list">
          <article v-for="user in dashboard.recent_users" :key="user.name">
            <span class="user-list-avatar"><UserRoundCheck :size="19" /></span>
            <div><strong>{{ user.full_name }}</strong><small>{{ user.name }}</small></div>
            <span class="table-status" :class="user.enabled ? 'success' : 'neutral'">{{ user.enabled ? "Active" : "Disabled" }}</span>
          </article>
          <p v-if="!dashboard.recent_users.length" class="users-empty">No users in this scope.</p>
        </div>
      </section>
      <section class="panel">
        <header class="panel-header"><div><h2>Role assignment</h2><p>Platform roles currently in use</p></div><ShieldCheck :size="19" /></header>
        <div class="role-distribution">
          <div v-for="item in dashboard.roles" :key="item.role"><span>{{ item.role }}</span><strong>{{ item.count }}</strong></div>
          <p v-if="!dashboard.roles.length" class="users-empty">No platform roles assigned.</p>
        </div>
      </section>
    </div>
  </template>
</template>
