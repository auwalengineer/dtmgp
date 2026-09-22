<script setup lang="ts">
import { ArrowUpRight, Briefcase, CircleAlert, Clock, Settings, TriangleAlert } from "@lucide/vue";
import { ref } from "vue";

import { apiRequest } from "@/services/api";

const LINKS = [
  { icon: Briefcase, label: "Background Jobs", description: "Queued and running background jobs (Frappe RQ)", href: "/app/rq-job" },
  { icon: Clock, label: "Scheduled Tasks", description: "Configured scheduled job types and their last run", href: "/app/scheduled-job-type" },
  { icon: TriangleAlert, label: "Error Log", description: "Unhandled server-side exceptions", href: "/app/error-log" },
  { icon: Settings, label: "Application Settings", description: "Site-wide Frappe/ERPNext system settings", href: "/app/system-settings" },
];

const schedulerActive = ref<boolean | null>(null);
const error = ref("");
async function load() {
  error.value = "";
  try {
    const result = await apiRequest<{ scheduler_active: boolean }>("/api/method/dtmgp.api.v1.administration.get_system_health");
    schedulerActive.value = result.scheduler_active;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load system health"; }
}
load();
</script>

<template>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section class="admin-metrics" aria-label="System health" style="grid-template-columns: repeat(1, 1fr); margin-bottom: 20px">
    <article><span class="admin-metric-icon" :class="schedulerActive ? 'green' : 'red'"><CircleAlert :size="20" /></span><div><small>Background scheduler</small><strong>{{ schedulerActive === null ? "Checking..." : (schedulerActive ? "Running" : "Inactive") }}</strong></div></article>
  </section>

  <div class="panel">
    <header class="panel-header"><div><h2>Frappe Desk tools</h2><p>System Operations is native Frappe/ERPNext functionality — reached here rather than rebuilt, since Desk already serves it live.</p></div></header>
    <div class="admin-user-list">
      <a v-for="link in LINKS" :key="link.href" class="action-link" :href="link.href" target="_blank" rel="noopener" style="display: contents">
        <article>
          <span class="user-list-avatar"><component :is="link.icon" :size="18" /></span>
          <div><strong>{{ link.label }}</strong><small>{{ link.description }}</small></div>
          <ArrowUpRight :size="16" />
        </article>
      </a>
    </div>
  </div>
</template>
