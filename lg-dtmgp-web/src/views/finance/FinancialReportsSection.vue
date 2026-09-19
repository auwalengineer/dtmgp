<script setup lang="ts">
import { BookOpenText, PenLine, Scale, Waves } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money } from "./types";
import type { Dashboard } from "./types";

defineProps<{ dashboard: Dashboard | null }>();

const ITEM_LABELS: Record<string, string> = { "budget-performance-report": "Budget Performance Report", "revenue-performance-report": "Revenue Performance Report", "expenditure-report": "Expenditure Report", "cash-flow-report": "Cash Flow Report", "trial-balance": "Trial Balance", "general-ledger-report": "General Ledger Report" };
const DEFAULT_ITEM = "budget-performance-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'budget-performance-report'">
    <PreviewCard :icon="PenLine" title="Budget performance report" body="A budget-versus-actual report isn't available yet — it depends on the Budget domain being connected first." />
  </template>

  <template v-else-if="activeItem === 'revenue-performance-report' && dashboard">
    <section class="finance-metrics" aria-label="Revenue performance report">
      <article><div><small>Assessed</small><strong>{{ money(dashboard.revenue.assessed) }}</strong></div></article>
      <article><div><small>Collected</small><strong>{{ money(dashboard.revenue.collected) }}</strong></div></article>
      <article><div><small>Outstanding</small><strong>{{ money(dashboard.revenue.outstanding) }}</strong></div></article>
    </section>
    <p class="users-empty">See Revenue for the head-by-head reconciliation behind these totals.</p>
  </template>

  <template v-else-if="activeItem === 'expenditure-report' && dashboard">
    <section class="finance-metrics" aria-label="Expenditure report">
      <article><div><small>Pending payments</small><strong>{{ money(dashboard.payments.pending) }}</strong></div></article>
      <article><div><small>Paid</small><strong>{{ money(dashboard.payments.paid) }}</strong></div></article>
    </section>
    <p class="users-empty">See Expenditure for the per-request detail behind these totals.</p>
  </template>

  <template v-else-if="activeItem === 'cash-flow-report'">
    <PreviewCard :icon="Waves" title="Cash flow report" body="A cash flow report isn't available yet." />
  </template>

  <template v-else-if="activeItem === 'trial-balance'">
    <PreviewCard :icon="Scale" title="Trial balance" body="A trial balance report isn't available yet." />
  </template>

  <template v-else-if="activeItem === 'general-ledger-report'">
    <PreviewCard :icon="BookOpenText" title="General ledger report" body="A general ledger report isn't available yet." />
  </template>
</template>
