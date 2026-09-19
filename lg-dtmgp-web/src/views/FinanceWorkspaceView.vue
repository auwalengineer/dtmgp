<script setup lang="ts">
import { Banknote, CircleAlert, Landmark, ShoppingCart } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import AccountingSection from "./finance/AccountingSection.vue";
import AllocationsSection from "./finance/AllocationsSection.vue";
import AuditControlSection from "./finance/AuditControlSection.vue";
import BudgetSection from "./finance/BudgetSection.vue";
import ContractsSection from "./finance/ContractsSection.vue";
import ExpenditureSection from "./finance/ExpenditureSection.vue";
import FinancialReportsSection from "./finance/FinancialReportsSection.vue";
import ProcurementSection from "./finance/ProcurementSection.vue";
import RevenueSection from "./finance/RevenueSection.vue";
import { money, today } from "./finance/types";
import type { AuditQuery, Dashboard, Options, PaymentRequest, ProcurementCase, ProcurementPlan, RevenueAssessment, RevenueHead, RevenueReceipt } from "./finance/types";

const TAB_LABELS = ["Budget", "Revenue", "Allocations", "Expenditure", "Accounting", "Procurement", "Contracts", "Audit & Control", "Financial Reports"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = { budget: "Budget", revenue: "Revenue", allocations: "Allocations", expenditure: "Expenditure", accounting: "Accounting", procurement: "Procurement", contracts: "Contracts", "audit-control": "Audit & Control", "financial-reports": "Financial Reports" };

const session = useSessionStore();
const route = useRoute();
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || TAB_LABELS[0]);
const dashboard = ref<Dashboard | null>(null);
const options = ref<Options>({ departments: [], accounts: [], cost_centers: [], fiscal_years: [], revenue_heads: [], procurement_plans: [] });
const revenueHeads = ref<RevenueHead[]>([]);
const revenueAssessments = ref<RevenueAssessment[]>([]);
const revenueReceipts = ref<RevenueReceipt[]>([]);
const paymentRequests = ref<PaymentRequest[]>([]);
const procurementPlans = ref<ProcurementPlan[]>([]);
const procurementCases = ref<ProcurementCase[]>([]);
const auditQueries = ref<AuditQuery[]>([]);
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const formKind = ref<"receipt" | "payment" | "plan" | "query">("receipt");
const form = ref<Record<string, string | number>>({});
const saving = ref(false);

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }
async function listRecords<T>(doctype: string): Promise<T[]> {
  const result = await apiRequest<{ items: T[] }>(`/api/method/dtmgp.api.v1.finance.list_records?doctype=${encodeURIComponent(doctype)}&${scopeQuery()}&page_size=100`);
  return result.items;
}

async function loadModule() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    [dashboard.value, options.value] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.finance.get_dashboard?${scopeQuery()}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.finance.get_form_options?${scopeQuery()}`),
    ]);
    await selectTab(activeTab.value);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load the finance workspace"; }
  finally { loading.value = false; }
}

async function loadRevenue() {
  [revenueHeads.value, revenueAssessments.value, revenueReceipts.value] = await Promise.all([
    listRecords<RevenueHead>("DTMGP Revenue Head"),
    listRecords<RevenueAssessment>("DTMGP Revenue Assessment"),
    listRecords<RevenueReceipt>("DTMGP Revenue Receipt"),
  ]);
}
async function loadExpenditure() { paymentRequests.value = await listRecords<PaymentRequest>("DTMGP Payment Request"); }
async function loadProcurement() {
  [procurementPlans.value, procurementCases.value] = await Promise.all([
    listRecords<ProcurementPlan>("DTMGP Procurement Plan"),
    listRecords<ProcurementCase>("DTMGP Procurement Case"),
  ]);
}
async function loadAuditControl() { auditQueries.value = await listRecords<AuditQuery>("DTMGP Audit Query"); }

async function selectTab(tab: Tab) {
  activeTab.value = tab;
  if (tab === "Revenue") await loadRevenue();
  else if (tab === "Expenditure") await loadExpenditure();
  else if (tab === "Procurement") await loadProcurement();
  else if (tab === "Audit & Control") await loadAuditControl();
}
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) selectTab(mapped); });
watch(() => session.activeLga, loadModule, { immediate: true });

function openForm(kind: typeof formKind.value, initial: Record<string, string | number>) { formKind.value = kind; form.value = initial; showForm.value = true; }
async function saveForm() {
  saving.value = true;
  error.value = "";
  const doctype: Record<typeof formKind.value, string> = { receipt: "DTMGP Revenue Receipt", payment: "DTMGP Payment Request", plan: "DTMGP Procurement Plan", query: "DTMGP Audit Query" };
  try {
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: doctype[formKind.value], values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the record"; }
  finally { saving.value = false; }
}

async function submitReceipt(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.finance.submit_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Revenue Receipt", name }) }); await loadRevenue(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to submit the receipt"; } }
async function advancePayment(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Payment Request", name, target_status: target }) }); await loadExpenditure(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the payment request"; } }
async function advancePlan(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Procurement Plan", name, target_status: target }) }); await loadProcurement(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the plan"; } }
async function advanceCase(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Procurement Case", name, target_status: target }) }); await loadProcurement(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the case"; } }
async function advanceQuery(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Audit Query", name, target_status: target }) }); await loadAuditControl(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the audit query"; } }
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ shortLga() }}</p><h1>Finance, Revenue & Procurement</h1><p>Budget, revenue, allocations, expenditure, accounting, procurement, contracts and audit</p></div></section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading financial records...</section>
  <template v-else-if="dashboard">
    <section class="finance-metrics" aria-label="Finance summary">
      <article><span class="hr-metric-icon green"><Banknote :size="19" /></span><div><small>Revenue collected</small><strong>{{ money(dashboard.revenue.collected) }}</strong><p>{{ money(dashboard.revenue.outstanding) }} outstanding</p></div></article>
      <article><span class="hr-metric-icon blue"><ShoppingCart :size="19" /></span><div><small>Active procurement</small><strong>{{ dashboard.procurement.active }}</strong><p>{{ dashboard.procurement.pending_approval }} awaiting approval</p></div></article>
      <article><span class="hr-metric-icon gold"><Landmark :size="19" /></span><div><small>Pending payments</small><strong>{{ money(dashboard.payments.pending) }}</strong><p>{{ money(dashboard.payments.paid) }} paid</p></div></article>
      <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Open audit queries</small><strong>{{ dashboard.audit.open_queries }}</strong><p>{{ dashboard.audit.overdue_queries }} overdue</p></div></article>
    </section>

    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="Finance views"><button v-for="tab in TAB_LABELS" :key="tab" :class="{ active: activeTab === tab }" @click="selectTab(tab)">{{ tab }}</button></nav>

      <BudgetSection v-if="activeTab === 'Budget'" />
      <RevenueSection v-else-if="activeTab === 'Revenue'" :revenue-heads="revenueHeads" :revenue-assessments="revenueAssessments" :revenue-receipts="revenueReceipts" :dashboard="dashboard" :can-manage="dashboard.can_manage" @new-receipt="openForm('receipt', { assessment: '', posting_date: today(), amount: 0, payment_channel: 'Cash', remarks: '' })" @submit-receipt="submitReceipt" />
      <AllocationsSection v-else-if="activeTab === 'Allocations'" />
      <ExpenditureSection v-else-if="activeTab === 'Expenditure'" :payment-requests="paymentRequests" :can-manage="dashboard.can_manage" @new-payment-request="openForm('payment', { request_date: today(), requesting_department: '', payee_type: 'Supplier', payee: '', description: '', amount: 0, expense_account: '', cost_center: '', justification: '' })" @advance-payment="advancePayment" />
      <AccountingSection v-else-if="activeTab === 'Accounting'" />
      <ProcurementSection v-else-if="activeTab === 'Procurement'" :procurement-plans="procurementPlans" :procurement-cases="procurementCases" :can-manage="dashboard.can_manage" @new-plan="openForm('plan', { fiscal_year: '', title: '', requesting_department: '', procurement_category: 'Goods', procurement_method: 'Open Competitive Bidding', estimated_amount: 0, budget_account: '', planned_start_date: today(), planned_end_date: today(), description: '' })" @advance-plan="advancePlan" @advance-case="advanceCase" />
      <ContractsSection v-else-if="activeTab === 'Contracts'" />
      <AuditControlSection v-else-if="activeTab === 'Audit & Control'" :audit-queries="auditQueries" :can-manage="dashboard.can_manage" @new-query="openForm('query', { query_date: today(), query_type: 'Finance', severity: 'Medium', subject: '', finding: '', recommendation: '', assigned_to: session.user.email, response_due_date: today() })" @advance-query="advanceQuery" />
      <FinancialReportsSection v-else-if="activeTab === 'Financial Reports'" :dashboard="dashboard" />
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal finance-modal" @submit.prevent="saveForm">
    <template v-if="formKind === 'receipt'"><h2>New revenue receipt</h2><div class="form-grid"><label>Assessment<select v-model="form.assessment" required><option value="" disabled>Select assessment</option><option v-for="item in revenueAssessments" :key="item.name" :value="item.name">{{ item.taxpayer_name }} — {{ item.name }}</option></select></label><label>Posting date<input v-model="form.posting_date" type="date" required /></label><label>Amount<input v-model.number="form.amount" type="number" min="0.01" step="0.01" required /></label><label>Payment channel<select v-model="form.payment_channel"><option>Cash</option><option>Bank Transfer</option><option>POS</option><option>Online</option></select></label><label class="full-field">Remarks<textarea v-model="form.remarks"></textarea></label></div></template>
    <template v-else-if="formKind === 'payment'"><h2>New payment request</h2><div class="form-grid"><label>Department<select v-model="form.requesting_department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Payee type<select v-model="form.payee_type"><option>Supplier</option><option>Employee</option><option>Other</option></select></label><label>Payee<input v-model="form.payee" required /></label><label>Amount<input v-model.number="form.amount" type="number" min="0.01" required /></label><label>Expense account<select v-model="form.expense_account" required><option value="" disabled>Select account</option><option v-for="item in options.accounts" :key="item">{{ item }}</option></select></label><label>Cost center<select v-model="form.cost_center" required><option value="" disabled>Select cost center</option><option v-for="item in options.cost_centers" :key="item">{{ item }}</option></select></label><label class="full-field">Description<input v-model="form.description" required /></label><label class="full-field">Justification<textarea v-model="form.justification" required></textarea></label></div></template>
    <template v-else-if="formKind === 'plan'"><h2>New procurement plan</h2><div class="form-grid"><label>Fiscal year<select v-model="form.fiscal_year" required><option value="" disabled>Select year</option><option v-for="item in options.fiscal_years" :key="item">{{ item }}</option></select></label><label>Title<input v-model="form.title" required /></label><label>Department<select v-model="form.requesting_department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Category<select v-model="form.procurement_category"><option>Goods</option><option>Works</option><option>Services</option><option>Consultancy</option></select></label><label>Method<select v-model="form.procurement_method"><option>Open Competitive Bidding</option><option>Restricted Tendering</option><option>Request for Quotations</option><option>Direct Procurement</option><option>Consultant Selection</option></select></label><label>Estimated amount<input v-model.number="form.estimated_amount" type="number" min="0.01" required /></label><label>Budget account<select v-model="form.budget_account" required><option value="" disabled>Select account</option><option v-for="item in options.accounts" :key="item">{{ item }}</option></select></label><label>Planned end<input v-model="form.planned_end_date" type="date" required /></label><label class="full-field">Description<textarea v-model="form.description" required></textarea></label></div></template>
    <template v-else-if="formKind === 'query'"><h2>New audit query</h2><div class="form-grid"><label>Area<select v-model="form.query_type"><option>Finance</option><option>Revenue</option><option>Procurement</option><option>Stores</option><option>Compliance</option></select></label><label>Severity<select v-model="form.severity"><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></label><label class="full-field">Subject<input v-model="form.subject" required /></label><label>Assigned to<input v-model="form.assigned_to" type="email" required /></label><label>Response due<input v-model="form.response_due_date" type="date" required /></label><label class="full-field">Finding<textarea v-model="form.finding" required></textarea></label><label class="full-field">Recommendation<textarea v-model="form.recommendation"></textarea></label></div></template>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save record" }}</button></footer>
  </form></div>
</template>
