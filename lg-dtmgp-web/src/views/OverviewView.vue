<script setup lang="ts">
import { ArrowRight, Building2, ShieldCheck, UserRoundCheck, UserRoundX, UsersRound } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Overview {
  scope: string;
  lga_count: number;
  user_count: number;
  active_user_count: number;
  disabled_user_count: number;
  unassigned_role_count: number;
  can_manage_users: boolean;
  is_statewide: boolean;
  workforce: { total: number; active: number; needs_attention: number } | null;
}

const session = useSessionStore();
const overview = ref<Overview | null>(null);
const loading = ref(true);
const error = ref("");
const greeting = computed(() => session.user.name.split(" ")[0] || "colleague");
const dateLabel = new Intl.DateTimeFormat("en-NG", { dateStyle: "full" }).format(new Date());
const metrics = computed(() => {
  if (!overview.value) return [];
  if (overview.value.workforce) return [
    { label: "Workforce records", value: overview.value.workforce.total, detail: overview.value.scope, tone: "green", icon: UsersRound },
    { label: "Active employees", value: overview.value.workforce.active, detail: "Current employment status", tone: "blue", icon: UserRoundCheck },
    { label: "Records requiring review", value: overview.value.workforce.needs_attention, detail: "Verification outstanding", tone: "red", icon: UserRoundX },
    { label: "System users", value: overview.value.active_user_count, detail: `${overview.value.disabled_user_count} disabled`, tone: "gold", icon: ShieldCheck },
  ];
  return [
    { label: "LGAs in scope", value: overview.value.lga_count, detail: overview.value.scope, tone: "green", icon: Building2 },
    { label: "Staff accounts", value: overview.value.user_count, detail: "Authorized scope only", tone: "blue", icon: ShieldCheck },
    { label: "Active accounts", value: overview.value.active_user_count, detail: "Enabled system users", tone: "green", icon: UserRoundCheck },
    { label: "Disabled accounts", value: overview.value.disabled_user_count, detail: `${overview.value.unassigned_role_count} without platform role`, tone: "red", icon: UserRoundX },
  ];
});

async function loadOverview() {
  loading.value = true;
  error.value = "";
  try {
    const company = session.activeLga ? `?company=${encodeURIComponent(session.activeLga)}` : "";
    overview.value = await apiRequest<Overview>(`/api/method/dtmgp.api.v1.overview.get_overview${company}`);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load overview";
  } finally {
    loading.value = false;
  }
}

watch(() => session.activeLga, loadOverview, { immediate: true });
</script>

<template>
  <section class="page-heading">
    <div>
      <p class="eyebrow">{{ overview?.scope || "Authorized operations" }}</p>
      <h1>Good morning, {{ greeting }}</h1>
      <p>{{ dateLabel }} · Access-controlled overview</p>
    </div>
    <RouterLink v-if="overview?.can_manage_users" class="primary-action action-link" to="/administration">
      Open administration <ArrowRight :size="17" />
    </RouterLink>
  </section>

  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading authorized overview...</section>
  <template v-else-if="overview">
    <section class="metrics-grid" aria-label="Authorized operational summary">
      <article v-for="metric in metrics" :key="metric.label" class="metric" :class="`metric--${metric.tone}`">
        <span class="metric-heading"><component :is="metric.icon" :size="17" />{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.detail }}</small>
      </article>
    </section>

    <div class="overview-grid">
      <section class="panel access-summary">
        <header class="panel-header"><div><h2>Your access boundary</h2><p>Calculated by the server from your roles and LGA permissions</p></div></header>
        <div class="access-summary-body">
          <ShieldCheck :size="30" />
          <div><strong>{{ overview.scope }}</strong><p>{{ overview.is_statewide ? "State role recognized. Metrics remain filtered by the active LGA selection." : "Your account is locked to its assigned Local Government Area." }}</p></div>
        </div>
      </section>
      <section class="panel workspace-links">
        <header class="panel-header"><div><h2>Workspaces</h2><p>Available for your current role</p></div></header>
        <RouterLink v-if="overview.workforce" to="/people"><UsersRound :size="19" /><span><strong>People & HR</strong><small>Employees, verification, leave and establishment</small></span><ArrowRight :size="16" /></RouterLink>
        <RouterLink v-if="overview.can_manage_users" to="/administration"><ShieldCheck :size="19" /><span><strong>Administration</strong><small>Users, roles and LGA access</small></span><ArrowRight :size="16" /></RouterLink>
      </section>
    </div>
  </template>
</template>
