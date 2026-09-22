<script setup lang="ts">
import { ClipboardList, FilePlus2, Plus, ScrollText, Trash2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money } from "./types";
import type { Budget, BudgetPerformanceRow } from "./types";

const props = defineProps<{ canManage: boolean; fiscalYears: string[]; costCenters: string[]; chartAccounts: string[] }>();
const session = useSessionStore();

const ITEM_LABELS: Record<string, string> = { "budget-preparation": "Budget Preparation", "budget-proposals": "Budget Proposals", "budget-review": "Budget Review", "approved-budget": "Approved Budget", "budget-revisions": "Budget Revisions", "budget-performance": "Budget Performance", "variance-analysis": "Variance Analysis" };
const DEFAULT_ITEM = "budget-preparation";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const loading = ref(true);
const error = ref("");
const budgets = ref<Budget[]>([]);
const performance = ref<BudgetPerformanceRow[]>([]);
const performanceFiscalYear = ref(props.fiscalYears[0] || "");

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function loadBudgets() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try { budgets.value = (await apiRequest<{ items: Budget[] }>(`/api/method/dtmgp.api.v1.finance.list_budgets?${scopeQuery()}`)).items; }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load budgets"; }
  finally { loading.value = false; }
}
async function loadPerformance() {
  if (!session.activeLga || !performanceFiscalYear.value) { performance.value = []; return; }
  error.value = "";
  try { performance.value = (await apiRequest<{ rows: BudgetPerformanceRow[] }>(`/api/method/dtmgp.api.v1.finance.get_budget_performance?${scopeQuery()}&fiscal_year=${encodeURIComponent(performanceFiscalYear.value)}`)).rows; }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load budget performance"; }
}
watch(() => session.activeLga, () => { loadBudgets(); loadPerformance(); }, { immediate: true });
watch(performanceFiscalYear, loadPerformance);

const draftBudgets = computed(() => budgets.value.filter((b) => b.docstatus === 0));
const approvedBudgets = computed(() => budgets.value.filter((b) => b.docstatus === 1));
const revisedBudgets = computed(() => budgets.value.filter((b) => b.amended_from));

const saving = ref(false);
async function submit(name: string) {
  error.value = "";
  try { await apiRequest("/api/method/dtmgp.api.v1.finance.submit_budget", { method: "POST", body: JSON.stringify({ name }) }); await loadBudgets(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to submit the budget"; }
}
async function amend(name: string) {
  error.value = "";
  try { await apiRequest("/api/method/dtmgp.api.v1.finance.cancel_budget", { method: "POST", body: JSON.stringify({ name }) }); await apiRequest("/api/method/dtmgp.api.v1.finance.amend_budget", { method: "POST", body: JSON.stringify({ name }) }); await loadBudgets(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to amend the budget"; }
}

const showNewForm = ref(false);
const newForm = ref({ fiscal_year: "", budget_against: "Cost Center", cost_center: "", project: "" });
const rows = ref<{ account: string; budget_amount: number }[]>([{ account: "", budget_amount: 0 }]);
function addRow() { rows.value.push({ account: "", budget_amount: 0 }); }
function removeRow(index: number) { rows.value.splice(index, 1); }
function resetNewForm() {
  newForm.value = { fiscal_year: "", budget_against: "Cost Center", cost_center: "", project: "" };
  rows.value = [{ account: "", budget_amount: 0 }];
}
async function createBudget() {
  saving.value = true;
  error.value = "";
  try {
    const accounts = rows.value.filter((row) => row.account && row.budget_amount > 0);
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_budget", {
      method: "POST",
      body: JSON.stringify({ company: session.activeLga, fiscal_year: newForm.value.fiscal_year, budget_against: newForm.value.budget_against, cost_center: newForm.value.cost_center || undefined, project: newForm.value.project || undefined, accounts }),
    });
    showNewForm.value = false;
    resetNewForm();
    await loadBudgets();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to create the budget"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading budgets...</p>

  <template v-else>
    <template v-if="activeItem === 'budget-preparation'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Draft budgets</h3><button v-if="canManage" class="secondary-action" @click="showNewForm = true"><FilePlus2 :size="15" /> New budget</button></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Budget</th><th>Fiscal year</th><th>Against</th><th>Total</th><th></th></tr></thead><tbody><tr v-for="item in draftBudgets" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.fiscal_year }}</td><td>{{ item.budget_against }}: {{ item.cost_center || item.project }}</td><td>{{ money(item.total_budget) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="submit(item.name)">Submit</button></td></tr></tbody></table><p v-if="!draftBudgets.length" class="users-empty">No draft budgets for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'budget-proposals'">
      <PreviewCard :icon="ScrollText" title="Budget proposals" body="Departmental budget proposal intake isn't available yet -- budgets are prepared directly against a cost center." />
    </template>

    <template v-else-if="activeItem === 'budget-review'">
      <PreviewCard :icon="ClipboardList" title="Budget review" body="A budget review and comment workflow isn't available yet -- a draft budget is submitted directly." />
    </template>

    <template v-else-if="activeItem === 'approved-budget'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Budget</th><th>Fiscal year</th><th>Against</th><th>Total</th><th></th></tr></thead><tbody><tr v-for="item in approvedBudgets" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.fiscal_year }}</td><td>{{ item.budget_against }}: {{ item.cost_center || item.project }}</td><td>{{ money(item.total_budget) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="amend(item.name)">Cancel &amp; revise</button></td></tr></tbody></table><p v-if="!approvedBudgets.length" class="users-empty">No approved budgets for this LGA yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'budget-revisions'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Budget</th><th>Amended from</th><th>Fiscal year</th><th>Total</th></tr></thead><tbody><tr v-for="item in revisedBudgets" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.amended_from }}</td><td>{{ item.fiscal_year }}</td><td>{{ money(item.total_budget) }}</td></tr></tbody></table><p v-if="!revisedBudgets.length" class="users-empty">No budget revisions recorded yet -- use "Cancel &amp; revise" on an approved budget to start one.</p></div>
    </template>

    <template v-else-if="activeItem === 'budget-performance' || activeItem === 'variance-analysis'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">{{ activeItem === 'budget-performance' ? 'Budget performance' : 'Variance analysis' }}</h3><label>Fiscal year<select v-model="performanceFiscalYear"><option value="" disabled>Select year</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Account</th><th>Budget</th><th>Actual</th><th>Variance</th></tr></thead><tbody><tr v-for="row in performance" :key="row.account"><td>{{ row.account }}</td><td>{{ money(row.budget) }}</td><td>{{ money(row.actual) }}</td><td>{{ money(row.variance) }}</td></tr></tbody></table><p v-if="!performance.length" class="users-empty">No submitted budget for this fiscal year yet.</p></div>
    </template>
  </template>

  <div v-if="showNewForm" class="modal-backdrop" @click.self="showNewForm = false"><form class="user-modal finance-modal" @submit.prevent="createBudget">
    <h2>New budget</h2>
    <div class="form-grid">
      <label>Fiscal year<select v-model="newForm.fiscal_year" required><option value="" disabled>Select year</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label>
      <label>Budget against<select v-model="newForm.budget_against"><option>Cost Center</option><option>Project</option></select></label>
      <label v-if="newForm.budget_against === 'Cost Center'">Cost center<select v-model="newForm.cost_center" required><option value="" disabled>Select cost center</option><option v-for="item in costCenters" :key="item">{{ item }}</option></select></label>
      <label v-else>Project<input v-model="newForm.project" required /></label>
    </div>
    <h3>Budget lines</h3>
    <div v-for="(row, index) in rows" :key="index" class="form-grid" style="border-bottom:1px solid var(--border-color, #e5e5e5);padding-bottom:8px;margin-bottom:8px">
      <label>Account<select v-model="row.account" required><option value="" disabled>Select account</option><option v-for="item in chartAccounts" :key="item">{{ item }}</option></select></label>
      <label>Budget amount<input v-model.number="row.budget_amount" type="number" min="0.01" step="0.01" required /></label>
      <button type="button" class="secondary-action compact-action" @click="removeRow(index)"><Trash2 :size="14" /> Remove</button>
    </div>
    <button type="button" class="secondary-action compact-action" @click="addRow"><Plus :size="14" /> Add line</button>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showNewForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save budget" }}</button></footer>
  </form></div>
</template>
