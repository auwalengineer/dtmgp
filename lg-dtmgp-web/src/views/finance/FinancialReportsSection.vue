<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";
import ReportActions from "@/components/ReportActions.vue";

import ItemTabs from "../shared/ItemTabs.vue";
import { money } from "./types";
import type { BudgetPerformanceRow, Dashboard, GLEntryRow, TrialBalanceRow } from "./types";

const props = defineProps<{ dashboard: Dashboard | null; fiscalYears: string[] }>();
const session = useSessionStore();

const ITEM_LABELS: Record<string, string> = { "budget-performance-report": "Budget Performance Report", "revenue-performance-report": "Revenue Performance Report", "expenditure-report": "Expenditure Report", "cash-flow-report": "Cash Flow Report", "trial-balance": "Trial Balance", "general-ledger-report": "General Ledger Report" };
const DEFAULT_ITEM = "budget-performance-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const fiscalYear = ref(props.fiscalYears[0] || "");
const budgetPerformance = ref<BudgetPerformanceRow[]>([]);
const cashFlow = ref<{ inflow: number; outflow: number; net: number } | null>(null);
const trialBalance = ref<{ rows: TrialBalanceRow[]; total_debit: number; total_credit: number } | null>(null);
const glEntries = ref<GLEntryRow[]>([]);
const loaded = new Set<string>();

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function loadTab(item: string) {
  if (!session.activeLga) return;
  if (item === "budget-performance-report" && fiscalYear.value) budgetPerformance.value = (await apiRequest<{ rows: BudgetPerformanceRow[] }>(`/api/method/dtmgp.api.v1.finance.get_budget_performance?${scopeQuery()}&fiscal_year=${encodeURIComponent(fiscalYear.value)}`)).rows;
  else if (item === "cash-flow-report") cashFlow.value = await apiRequest(`/api/method/dtmgp.api.v1.finance.get_cash_flow?${scopeQuery()}${fiscalYear.value ? `&fiscal_year=${encodeURIComponent(fiscalYear.value)}` : ""}`);
  else if (item === "trial-balance" && !loaded.has("trial-balance")) { trialBalance.value = await apiRequest(`/api/method/dtmgp.api.v1.finance.get_trial_balance?${scopeQuery()}${fiscalYear.value ? `&fiscal_year=${encodeURIComponent(fiscalYear.value)}` : ""}`); loaded.add("trial-balance"); }
  else if (item === "general-ledger-report" && !loaded.has("general-ledger-report")) { glEntries.value = (await apiRequest<{ items: GLEntryRow[] }>(`/api/method/dtmgp.api.v1.finance.list_gl_entries?${scopeQuery()}`)).items; loaded.add("general-ledger-report"); }
}
watch(activeItem, (item) => loadTab(item), { immediate: true });
watch(fiscalYear, () => { loaded.delete("trial-balance"); loadTab(activeItem.value); });
const exportData = computed(() => {
  if (activeItem.value === "revenue-performance-report" && props.dashboard) return { id: "finance.revenue-performance", columns: ["Measure", "Amount"], rows: [["Assessed", props.dashboard.revenue.assessed], ["Collected", props.dashboard.revenue.collected], ["Outstanding", props.dashboard.revenue.outstanding]] };
  if (activeItem.value === "expenditure-report" && props.dashboard) return { id: "finance.expenditure", columns: ["Measure", "Amount"], rows: [["Pending payments", props.dashboard.payments.pending], ["Paid", props.dashboard.payments.paid]] };
  if (activeItem.value === "cash-flow-report") return { id: "finance.cash-flow", columns: ["Measure", "Amount"], rows: cashFlow.value ? [["Inflow", cashFlow.value.inflow], ["Outflow", cashFlow.value.outflow], ["Net", cashFlow.value.net]] : [] };
  if (activeItem.value === "trial-balance") return { id: "finance.trial-balance", columns: ["Account", "Root type", "Debit", "Credit"], rows: (trialBalance.value?.rows || []).map(row => [row.account, row.root_type, row.debit, row.credit]) };
  if (activeItem.value === "general-ledger-report") return { id: "finance.general-ledger", columns: ["Date", "Account", "Debit", "Credit", "Voucher"], rows: glEntries.value.map(row => [row.posting_date, row.account, row.debit, row.credit, `${row.voucher_type} ${row.voucher_no}`]) };
  return { id: "finance.budget-performance", columns: ["Account", "Budget", "Actual", "Variance"], rows: budgetPerformance.value.map(row => [row.account, row.budget, row.actual, row.variance]) };
});
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <ReportActions :report-id="exportData.id" :title="ITEM_LABELS[activeItem]" :columns="exportData.columns" :rows="exportData.rows" :company="session.activeLga" :filters="fiscalYear ? { 'Fiscal year': fiscalYear } : { Period: 'All time' }" />

  <template v-if="activeItem === 'budget-performance-report'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Budget performance report</h3><label>Fiscal year<select v-model="fiscalYear"><option value="" disabled>Select year</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Account</th><th>Budget</th><th>Actual</th><th>Variance</th></tr></thead><tbody><tr v-for="row in budgetPerformance" :key="row.account"><td>{{ row.account }}</td><td>{{ money(row.budget) }}</td><td>{{ money(row.actual) }}</td><td>{{ money(row.variance) }}</td></tr></tbody></table><p v-if="!budgetPerformance.length" class="users-empty">No submitted budget for this fiscal year yet -- see Budget &gt; Budget Preparation.</p></div>
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
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Cash flow report</h3><label>Fiscal year<select v-model="fiscalYear"><option value="">All time</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
    <section class="finance-metrics" aria-label="Cash flow" v-if="cashFlow">
      <article><div><small>Inflow (revenue collected)</small><strong>{{ money(cashFlow.inflow) }}</strong></div></article>
      <article><div><small>Outflow (payments made)</small><strong>{{ money(cashFlow.outflow) }}</strong></div></article>
      <article><div><small>Net</small><strong>{{ money(cashFlow.net) }}</strong></div></article>
    </section>
  </template>

  <template v-else-if="activeItem === 'trial-balance'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Trial balance</h3><label>Fiscal year<select v-model="fiscalYear"><option value="">All time</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
    <div class="staff-table-wrap" v-if="trialBalance"><table class="staff-table finance-table"><thead><tr><th>Account</th><th>Root type</th><th>Debit</th><th>Credit</th></tr></thead><tbody><tr v-for="row in trialBalance.rows" :key="row.account"><td>{{ row.account }}</td><td>{{ row.root_type }}</td><td>{{ money(row.debit) }}</td><td>{{ money(row.credit) }}</td></tr></tbody><tfoot><tr><td colspan="2"><strong>Total</strong></td><td><strong>{{ money(trialBalance.total_debit) }}</strong></td><td><strong>{{ money(trialBalance.total_credit) }}</strong></td></tr></tfoot></table><p v-if="!trialBalance.rows.length" class="users-empty">No ledger postings to report for this period.</p></div>
  </template>

  <template v-else-if="activeItem === 'general-ledger-report'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Date</th><th>Account</th><th>Debit</th><th>Credit</th><th>Voucher</th></tr></thead><tbody><tr v-for="row in glEntries" :key="row.name" v-record="{ doctype: 'GL Entry', name: row.name }"><td>{{ row.posting_date }}</td><td>{{ row.account }}</td><td>{{ money(row.debit) }}</td><td>{{ money(row.credit) }}</td><td>{{ row.voucher_type }} {{ row.voucher_no }}</td></tr></tbody></table><p v-if="!glEntries.length" class="users-empty">No general ledger postings for this LGA yet.</p></div>
  </template>
</template>
