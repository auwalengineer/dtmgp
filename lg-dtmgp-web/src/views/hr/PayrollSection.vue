<script setup lang="ts">
import { Banknote, ListChecks, Wallet } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { PayrollOverview } from "./types";

defineProps<{ payroll: PayrollOverview | null }>();

const ITEM_LABELS: Record<string, string> = { "salary-structures": "Salary Structures", "payroll-processing": "Payroll Processing", "salary-slips": "Salary Slips", deductions: "Deductions", "payroll-reports": "Payroll Reports" };
const DEFAULT_ITEM = "payroll-reports";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'salary-structures'">
    <PreviewCard :icon="ListChecks" title="Salary structures" body="Salary structure configuration (pay components, grade-level bands) isn't available yet — payroll amounts remain restricted pending finance/HR sign-off." />
  </template>

  <template v-else-if="activeItem === 'payroll-processing'">
    <PreviewCard :icon="Banknote" title="Payroll processing" body="A payroll run workflow (generate, review, disburse) isn't available yet — only draft/submitted/paid counts are visible today." />
  </template>

  <template v-else-if="activeItem === 'salary-slips' && payroll">
    <section class="hr-metrics" aria-label="Salary slips">
      <article><span class="hr-metric-icon gold"><Wallet :size="19" /></span><div><small>Draft slips</small><strong>{{ payroll.draft }}</strong></div></article>
      <article><span class="hr-metric-icon blue"><Wallet :size="19" /></span><div><small>Submitted</small><strong>{{ payroll.submitted }}</strong></div></article>
      <article><span class="hr-metric-icon green"><Wallet :size="19" /></span><div><small>Paid</small><strong>{{ payroll.paid }}</strong></div></article>
    </section>
    <p class="users-empty">Per-slip detail (amounts, deductions, bank references) remains deferred as Restricted data pending finance/payroll sign-off.</p>
  </template>

  <template v-else-if="activeItem === 'deductions'">
    <PreviewCard :icon="ListChecks" title="Deductions" body="Statutory and voluntary deduction detail isn't exposed yet — it falls under the same Restricted payroll data pending sign-off." />
  </template>

  <template v-else-if="activeItem === 'payroll-reports' && payroll">
    <section class="hr-metrics" aria-label="Payroll overview">
      <article><span class="hr-metric-icon gold"><Wallet :size="19" /></span><div><small>Draft salary slips</small><strong>{{ payroll.draft }}</strong></div></article>
      <article><span class="hr-metric-icon blue"><Wallet :size="19" /></span><div><small>Submitted</small><strong>{{ payroll.submitted }}</strong></div></article>
      <article><span class="hr-metric-icon green"><Wallet :size="19" /></span><div><small>Paid</small><strong>{{ payroll.paid }}</strong></div></article>
    </section>
    <p class="users-empty">Payroll processing, bank and deduction detail remain deferred pending finance/payroll sign-off (see docs/implementation-status.md).</p>
  </template>
</template>
