<script setup lang="ts">
import { ClipboardList, ShieldAlert } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { AuditExceptions } from "./types";

defineProps<{ auditExceptions: AuditExceptions | null }>();

const ITEM_LABELS: Record<string, string> = { "audit-exercises": "Audit Exercises", "audit-exceptions": "Audit Exceptions", "duplicate-records": "Duplicate Records", "staff-audit-reports": "Staff Audit Reports" };
const DEFAULT_ITEM = "audit-exceptions";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'audit-exercises'">
    <PreviewCard :icon="ClipboardList" title="Audit exercises" body="Staff audit is currently a stateless, on-demand report — there is no tracked audit-exercise entity (unlike staff verification, which runs as scheduled exercises)." />
  </template>

  <template v-else-if="activeItem === 'audit-exceptions' && auditExceptions">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Unverified staff</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Verification status</th></tr></thead><tbody><tr v-for="item in auditExceptions.unverified" :key="item.name"><td>{{ item.employee_name }}</td><td>{{ item.dtmgp_verification_status || 'Pending' }}</td></tr></tbody></table><p v-if="!auditExceptions.unverified.length" class="users-empty">No unverified staff.</p></div>
  </template>

  <template v-else-if="activeItem === 'duplicate-records' && auditExceptions">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Possible duplicate records</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Name</th><th>Date of birth</th><th>Employee IDs</th></tr></thead><tbody><tr v-for="(row, index) in auditExceptions.duplicate_candidates" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.date_of_birth }}</td><td>{{ row.employees.join(', ') }}</td></tr></tbody></table><p v-if="!auditExceptions.duplicate_candidates.length" class="users-empty">No duplicate candidates found.</p></div>
  </template>

  <template v-else-if="activeItem === 'staff-audit-reports' && auditExceptions">
    <section class="hr-metrics" aria-label="Staff audit summary">
      <article><span class="hr-metric-icon red"><ShieldAlert :size="19" /></span><div><small>Unverified staff</small><strong>{{ auditExceptions.unverified.length }}</strong></div></article>
      <article><span class="hr-metric-icon gold"><ShieldAlert :size="19" /></span><div><small>Possible duplicates</small><strong>{{ auditExceptions.duplicate_candidates.length }}</strong></div></article>
      <article><span class="hr-metric-icon blue"><ShieldAlert :size="19" /></span><div><small>Missing grade level</small><strong>{{ auditExceptions.missing_grade.length }}</strong></div></article>
    </section>
    <p class="users-empty">This is the same on-demand exception check as Audit Exceptions and Duplicate Records — a historical/trend audit report isn't available yet.</p>
  </template>
</template>
