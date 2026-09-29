<script setup lang="ts">
import { Receipt, TrendingUp, Users } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money, today } from "./types";
import type { Dashboard, RevenueAssessment, RevenueHead, RevenueReceipt } from "./types";

const props = defineProps<{ revenueHeads: RevenueHead[]; revenueAssessments: RevenueAssessment[]; revenueReceipts: RevenueReceipt[]; dashboard: Dashboard | null; canManage: boolean }>();
defineEmits<{ "new-receipt": []; "submit-receipt": [name: string] }>();

const ITEM_LABELS: Record<string, string> = { "revenue-sources": "Revenue Sources", "revenue-targets": "Revenue Targets", "revenue-collections": "Revenue Collections", "collection-channels": "Collection Channels", "revenue-officers": "Revenue Officers", "daily-collections": "Daily Collections", "revenue-performance": "Revenue Performance", "revenue-reconciliation": "Revenue Reconciliation" };
const DEFAULT_ITEM = "revenue-collections";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const channelTotals = computed(() => {
  const totals = new Map<string, number>();
  for (const receipt of props.revenueReceipts) totals.set(receipt.payment_channel || "Unspecified", (totals.get(receipt.payment_channel || "Unspecified") || 0) + Number(receipt.amount || 0));
  return [...totals.entries()].map(([channel, amount]) => ({ channel, amount })).sort((a, b) => b.amount - a.amount);
});
const dailyReceipts = computed(() => props.revenueReceipts.filter((receipt) => receipt.posting_date === today()));
const reconciliation = computed(() => props.revenueHeads.map((head) => {
  const assessed = props.revenueAssessments.filter((a) => a.revenue_head === head.name && a.status !== "Cancelled").reduce((sum, a) => sum + Number(a.amount || 0), 0);
  const assessmentNames = new Set(props.revenueAssessments.filter((a) => a.revenue_head === head.name).map((a) => a.name));
  const collected = props.revenueReceipts.filter((r) => assessmentNames.has(r.assessment)).reduce((sum, r) => sum + Number(r.amount || 0), 0);
  return { head: head.revenue_name, assessed, collected, outstanding: Math.max(assessed - collected, 0) };
}));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'revenue-sources'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Revenue head</th><th>Code</th><th>Rate type</th><th>Default rate</th><th>Status</th></tr></thead><tbody><tr v-for="head in revenueHeads" :key="head.name" v-record="{ doctype: 'DTMGP Revenue Head', name: head.name }"><td>{{ head.revenue_name }}</td><td>{{ head.revenue_code }}</td><td>{{ head.rate_type }}</td><td>{{ head.default_rate }}</td><td><span class="table-status" :class="head.disabled ? 'neutral' : 'success'">{{ head.disabled ? 'Disabled' : 'Active' }}</span></td></tr></tbody></table><p v-if="!revenueHeads.length" class="users-empty">No revenue heads configured for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'revenue-targets'">
    <PreviewCard :icon="TrendingUp" title="Revenue targets" body="Per-head revenue collection targets aren't modeled yet — revenue heads carry a default rate, not a target amount." />
  </template>

  <template v-else-if="activeItem === 'revenue-collections'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Revenue collections</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-receipt')"><Receipt :size="15" /> New receipt</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Assessment</th><th>Date</th><th>Amount</th><th>Channel</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="receipt in revenueReceipts" :key="receipt.name" v-record="{ doctype: 'DTMGP Revenue Receipt', name: receipt.name }"><td><strong>{{ receipt.name }}</strong></td><td>{{ receipt.assessment }}</td><td>{{ receipt.posting_date }}</td><td>{{ money(receipt.amount) }}</td><td>{{ receipt.payment_channel || '-' }}</td><td><span class="table-status" :class="receipt.docstatus === 1 ? 'success' : 'neutral'">{{ receipt.docstatus === 1 ? 'Submitted' : 'Draft' }}</span></td><td><button v-if="canManage && receipt.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-receipt', receipt.name)">Submit</button></td></tr></tbody></table><p v-if="!revenueReceipts.length" class="users-empty">No revenue collections recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'collection-channels'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Channel</th><th>Amount collected</th></tr></thead><tbody><tr v-for="row in channelTotals" :key="row.channel"><td>{{ row.channel }}</td><td>{{ money(row.amount) }}</td></tr></tbody></table><p v-if="!channelTotals.length" class="users-empty">No collections recorded to group by channel yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'revenue-officers'">
    <PreviewCard :icon="Users" title="Revenue officers" body="Assigning revenue collection to specific officers isn't modeled yet — receipts aren't currently linked to a collecting officer." />
  </template>

  <template v-else-if="activeItem === 'daily-collections'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Reference</th><th>Assessment</th><th>Amount</th><th>Channel</th></tr></thead><tbody><tr v-for="receipt in dailyReceipts" :key="receipt.name" v-record="{ doctype: 'DTMGP Revenue Receipt', name: receipt.name }"><td><strong>{{ receipt.name }}</strong></td><td>{{ receipt.assessment }}</td><td>{{ money(receipt.amount) }}</td><td>{{ receipt.payment_channel || '-' }}</td></tr></tbody></table><p v-if="!dailyReceipts.length" class="users-empty">No collections recorded today.</p></div>
  </template>

  <template v-else-if="activeItem === 'revenue-performance' && dashboard">
    <section class="finance-metrics" aria-label="Revenue performance">
      <article><div><small>Assessed</small><strong>{{ money(dashboard.revenue.assessed) }}</strong></div></article>
      <article><div><small>Collected</small><strong>{{ money(dashboard.revenue.collected) }}</strong></div></article>
      <article><div><small>Outstanding</small><strong>{{ money(dashboard.revenue.outstanding) }}</strong></div></article>
    </section>
  </template>

  <template v-else-if="activeItem === 'revenue-reconciliation'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Revenue head</th><th>Assessed</th><th>Collected</th><th>Outstanding</th></tr></thead><tbody><tr v-for="row in reconciliation" :key="row.head"><td>{{ row.head }}</td><td>{{ money(row.assessed) }}</td><td>{{ money(row.collected) }}</td><td>{{ money(row.outstanding) }}</td></tr></tbody></table><p v-if="!reconciliation.length" class="users-empty">No revenue heads to reconcile yet.</p></div>
  </template>
</template>
