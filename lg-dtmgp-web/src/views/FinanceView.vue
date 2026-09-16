<script setup lang="ts">
import { Banknote, CircleAlert, ClipboardCheck, FilePlus2, Landmark, Search, ShoppingCart } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Dashboard { scope: string; can_manage: boolean; revenue: { assessed: number; collected: number; outstanding: number }; procurement: { planned: number; active: number; pending_approval: number }; payments: { pending: number; paid: number }; audit: { open_queries: number; overdue_queries: number } }
interface RecordItem { name: string; [key: string]: string | number | null }
interface Options { departments: string[]; accounts: string[]; cost_centers: string[]; fiscal_years: string[]; revenue_heads: { name: string; revenue_name: string }[]; procurement_plans: { name: string; title: string }[] }

const session = useSessionStore();
const tabs = [
  { label: "Revenue", doctype: "DTMGP Revenue Assessment" },
  { label: "Procurement", doctype: "DTMGP Procurement Plan" },
  { label: "Payments", doctype: "DTMGP Payment Request" },
  { label: "Audit queries", doctype: "DTMGP Audit Query" },
];
const active = ref(tabs[0]);
const dashboard = ref<Dashboard | null>(null);
const options = ref<Options>({ departments: [], accounts: [], cost_centers: [], fiscal_years: [], revenue_heads: [], procurement_plans: [] });
const records = ref<RecordItem[]>([]);
const total = ref(0);
const search = ref("");
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string | number>>(emptyForm("Revenue"));

const columns = computed(() => {
  if (active.value.label === "Revenue") return [["taxpayer_name", "Payer"], ["revenue_head", "Revenue head"], ["amount", "Assessed"], ["amount_paid", "Paid"], ["status", "Status"]];
  if (active.value.label === "Procurement") return [["title", "Plan"], ["procurement_category", "Category"], ["procurement_method", "Method"], ["estimated_amount", "Estimate"], ["status", "Status"]];
  if (active.value.label === "Payments") return [["payee", "Payee"], ["description", "Description"], ["amount", "Amount"], ["request_date", "Requested"], ["status", "Status"]];
  return [["subject", "Subject"], ["query_type", "Area"], ["severity", "Severity"], ["response_due_date", "Due"], ["status", "Status"]];
});
const today = () => new Date().toISOString().slice(0, 10);
const money = (value: unknown) => new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(Number(value || 0));
const isMoney = (field: string) => ["amount", "amount_paid", "estimated_amount"].includes(field);

function emptyForm(tab: string) {
  const base = { company: session.activeLga };
  if (tab === "Revenue") return { ...base, revenue_head: "", taxpayer_name: "", taxpayer_id: "", assessment_date: today(), due_date: today(), amount: 0, notes: "" };
  if (tab === "Procurement") return { ...base, fiscal_year: "", title: "", requesting_department: "", procurement_category: "Goods", procurement_method: "Open Competitive Bidding", estimated_amount: 0, budget_account: "", planned_start_date: today(), planned_end_date: today(), status: "Draft", description: "" };
  if (tab === "Payments") return { ...base, request_date: today(), requesting_department: "", payee_type: "Supplier", payee: "", description: "", amount: 0, expense_account: "", cost_center: "", status: "Draft", justification: "" };
  return { ...base, query_date: today(), query_type: "Finance", severity: "Medium", subject: "", finding: "", recommendation: "", assigned_to: session.user.email, response_due_date: today(), status: "Open" };
}

async function loadModule() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [dashboard.value, options.value] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.finance.get_dashboard?company=${company}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.finance.get_form_options?company=${company}`),
    ]);
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load finance workspace"; }
  finally { loading.value = false; }
}
async function loadRecords() {
  const params = new URLSearchParams({ doctype: active.value.doctype, company: session.activeLga });
  if (search.value.trim()) params.set("search", search.value.trim());
  const result = await apiRequest<{ items: RecordItem[]; total: number }>(`/api/method/dtmgp.api.v1.finance.list_records?${params}`);
  records.value = result.items; total.value = result.total;
}
async function chooseTab(tab: typeof tabs[number]) { active.value = tab; search.value = ""; await loadRecords(); }
function openCreate() { form.value = emptyForm(active.value.label); showForm.value = true; }
async function saveRecord() {
  saving.value = true; error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: active.value.doctype, values: form.value }) });
    showForm.value = false; await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save record"; }
  finally { saving.value = false; }
}

watch(() => session.activeLga, loadModule, { immediate: true });
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ dashboard?.scope || session.activeLga }}</p><h1>Finance, Revenue & Procurement</h1><p>Treasury control, collections, purchasing and audit follow-up</p></div><button v-if="dashboard?.can_manage" class="primary-action" @click="openCreate"><FilePlus2 :size="17" /> New {{ active.label.toLowerCase().replace(' queries', ' query') }}</button></section>
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
      <nav class="hr-tabs" aria-label="Finance views"><button v-for="tab in tabs" :key="tab.label" :class="{ active: active.label === tab.label }" @click="chooseTab(tab)">{{ tab.label }}</button></nav>
      <form class="directory-toolbar" @submit.prevent="loadRecords"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" :placeholder="`Search ${active.label.toLowerCase()}`" /></label><button class="secondary-action">Search</button></form>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th v-for="column in columns" :key="column[0]">{{ column[1] }}</th></tr></thead><tbody><tr v-for="item in records" :key="item.name"><td><strong>{{ item.name }}</strong></td><td v-for="column in columns" :key="column[0]"><span v-if="column[0] === 'status' || column[0] === 'severity'" class="table-status" :class="item[column[0]] === 'Paid' || item[column[0]] === 'Closed' ? 'success' : 'neutral'">{{ item[column[0]] }}</span><template v-else>{{ isMoney(column[0]) ? money(item[column[0]]) : (item[column[0]] || '-') }}</template></td></tr></tbody></table><p v-if="!records.length" class="users-empty">No {{ active.label.toLowerCase() }} records in this LGA.</p><footer class="table-footer"><span>{{ total }} records</span><span>Scoped to {{ session.activeLga }}</span></footer></div>
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal finance-modal" @submit.prevent="saveRecord"><h2>New {{ active.label.replace(' queries', ' query') }}</h2><div class="form-grid">
    <template v-if="active.label === 'Revenue'"><label>Revenue head<select v-model="form.revenue_head" required><option value="" disabled>Select revenue head</option><option v-for="item in options.revenue_heads" :key="item.name" :value="item.name">{{ item.revenue_name }}</option></select></label><label>Payer<input v-model="form.taxpayer_name" required /></label><label>Tax ID / reference<input v-model="form.taxpayer_id" /></label><label>Assessment date<input v-model="form.assessment_date" type="date" required /></label><label>Due date<input v-model="form.due_date" type="date" required /></label><label>Amount<input v-model.number="form.amount" type="number" min="0.01" step="0.01" required /></label><label class="full-field">Notes<textarea v-model="form.notes"></textarea></label></template>
    <template v-else-if="active.label === 'Procurement'"><label>Fiscal year<select v-model="form.fiscal_year" required><option value="" disabled>Select year</option><option v-for="item in options.fiscal_years" :key="item">{{ item }}</option></select></label><label>Title<input v-model="form.title" required /></label><label>Department<select v-model="form.requesting_department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Category<select v-model="form.procurement_category"><option>Goods</option><option>Works</option><option>Services</option><option>Consultancy</option></select></label><label>Method<select v-model="form.procurement_method"><option>Open Competitive Bidding</option><option>Restricted Tendering</option><option>Request for Quotations</option><option>Direct Procurement</option><option>Consultant Selection</option></select></label><label>Estimated amount<input v-model.number="form.estimated_amount" type="number" min="0.01" required /></label><label>Budget account<select v-model="form.budget_account" required><option value="" disabled>Select account</option><option v-for="item in options.accounts" :key="item">{{ item }}</option></select></label><label>Planned end<input v-model="form.planned_end_date" type="date" required /></label><label class="full-field">Description<textarea v-model="form.description" required></textarea></label></template>
    <template v-else-if="active.label === 'Payments'"><label>Department<select v-model="form.requesting_department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Payee type<select v-model="form.payee_type"><option>Supplier</option><option>Employee</option><option>Other</option></select></label><label>Payee<input v-model="form.payee" required /></label><label>Amount<input v-model.number="form.amount" type="number" min="0.01" required /></label><label>Expense account<select v-model="form.expense_account" required><option value="" disabled>Select account</option><option v-for="item in options.accounts" :key="item">{{ item }}</option></select></label><label>Cost center<select v-model="form.cost_center" required><option value="" disabled>Select cost center</option><option v-for="item in options.cost_centers" :key="item">{{ item }}</option></select></label><label class="full-field">Description<input v-model="form.description" required /></label><label class="full-field">Justification<textarea v-model="form.justification" required></textarea></label></template>
    <template v-else><label>Area<select v-model="form.query_type"><option>Finance</option><option>Revenue</option><option>Procurement</option><option>Stores</option><option>Compliance</option></select></label><label>Severity<select v-model="form.severity"><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></label><label class="full-field">Subject<input v-model="form.subject" required /></label><label>Assigned to<input v-model="form.assigned_to" type="email" required /></label><label>Response due<input v-model="form.response_due_date" type="date" required /></label><label class="full-field">Finding<textarea v-model="form.finding" required></textarea></label><label class="full-field">Recommendation<textarea v-model="form.recommendation"></textarea></label></template>
  </div><p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save record' }}</button></footer></form></div>
</template>
