<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import { money } from "./types";
import type { AccountRow, GLEntryRow, JournalEntryRow, TrialBalanceRow } from "./types";

const props = defineProps<{ fiscalYears: string[] }>();
const session = useSessionStore();

const ITEM_LABELS: Record<string, string> = { "chart-of-accounts": "Chart of Accounts", "journal-entries": "Journal Entries", "general-ledger": "General Ledger", "accounts-receivable": "Accounts Receivable", "accounts-payable": "Accounts Payable", "bank-reconciliation": "Bank Reconciliation", "trial-balance": "Trial Balance" };
const DEFAULT_ITEM = "chart-of-accounts";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const loading = ref(false);
const error = ref("");
const accounts = ref<AccountRow[]>([]);
const journalEntries = ref<JournalEntryRow[]>([]);
const glEntries = ref<GLEntryRow[]>([]);
const trialBalance = ref<{ rows: TrialBalanceRow[]; total_debit: number; total_credit: number } | null>(null);
const ledgers = ref<{ receivables: Array<Record<string, string | number>>; payables: Array<Record<string, string | number>> }>({ receivables: [], payables: [] });
const banking = ref<{ accounts: Array<Record<string, string | number>>; transactions: Array<Record<string, string | number>>; signatories: Array<Record<string, string | number>>; voucher_print_formats: Array<Record<string, string | number>> }>({ accounts: [], transactions: [], signatories: [], voucher_print_formats: [] });
const trialBalanceFiscalYear = ref(props.fiscalYears[0] || "");
const loaded = new Set<string>();

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function loadTab(item: string) {
  if (loaded.has(item) && item !== "trial-balance") return;
  loading.value = true;
  error.value = "";
  try {
    if (item === "chart-of-accounts") accounts.value = (await apiRequest<{ items: AccountRow[] }>(`/api/method/dtmgp.api.v1.finance.get_accounts_tree?${scopeQuery()}`)).items;
    else if (item === "journal-entries") journalEntries.value = (await apiRequest<{ items: JournalEntryRow[] }>(`/api/method/dtmgp.api.v1.finance.list_journal_entries?${scopeQuery()}`)).items;
    else if (item === "general-ledger") glEntries.value = (await apiRequest<{ items: GLEntryRow[] }>(`/api/method/dtmgp.api.v1.finance.list_gl_entries?${scopeQuery()}`)).items;
    else if (["accounts-receivable", "accounts-payable"].includes(item)) ledgers.value = await apiRequest(`/api/method/dtmgp.api.v1.finance.get_receivables_payables?${scopeQuery()}`);
    else if (item === "bank-reconciliation") banking.value = await apiRequest(`/api/method/dtmgp.api.v1.finance.get_banking_setup?${scopeQuery()}`);
    else if (item === "trial-balance") trialBalance.value = await apiRequest(`/api/method/dtmgp.api.v1.finance.get_trial_balance?${scopeQuery()}${trialBalanceFiscalYear.value ? `&fiscal_year=${encodeURIComponent(trialBalanceFiscalYear.value)}` : ""}`);
    loaded.add(item);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load accounting records"; }
  finally { loading.value = false; }
}
watch(activeItem, (item) => loadTab(item), { immediate: true });
watch(() => session.activeLga, () => { loaded.clear(); loadTab(activeItem.value); });
watch(trialBalanceFiscalYear, () => { loaded.delete("trial-balance"); loadTab("trial-balance"); });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>

  <template v-else>
    <template v-if="activeItem === 'chart-of-accounts'">
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Account</th><th>Parent</th><th>Root type</th><th>Type</th></tr></thead><tbody><tr v-for="row in accounts" :key="row.name"><td :style="{ fontWeight: row.is_group ? 600 : 400 }">{{ row.account_name }}</td><td>{{ row.parent_account || '-' }}</td><td>{{ row.root_type }}</td><td>{{ row.account_type || '-' }}</td></tr></tbody></table><p v-if="!accounts.length" class="users-empty">No accounts found for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'journal-entries'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Date</th><th>Type</th><th>Total debit</th><th>Remark</th></tr></thead><tbody><tr v-for="row in journalEntries" :key="row.name"><td><strong>{{ row.name }}</strong></td><td>{{ row.posting_date }}</td><td>{{ row.voucher_type }}</td><td>{{ money(row.total_debit) }}</td><td>{{ row.user_remark || '-' }}</td></tr></tbody></table><p v-if="!journalEntries.length" class="users-empty">No submitted journal entries for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'general-ledger'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Date</th><th>Account</th><th>Debit</th><th>Credit</th><th>Against</th><th>Voucher</th></tr></thead><tbody><tr v-for="row in glEntries" :key="row.name"><td>{{ row.posting_date }}</td><td>{{ row.account }}</td><td>{{ money(row.debit) }}</td><td>{{ money(row.credit) }}</td><td>{{ row.against || '-' }}</td><td>{{ row.voucher_type }} {{ row.voucher_no }}</td></tr></tbody></table><p v-if="!glEntries.length" class="users-empty">No general ledger postings for this LGA yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'accounts-receivable'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Assessment</th><th>Ratepayer</th><th>Due</th><th>Assessed</th><th>Outstanding</th><th>Status</th></tr></thead><tbody><tr v-for="row in ledgers.receivables" :key="String(row.name)"><td>{{ row.name }}</td><td>{{ row.party }}</td><td>{{ row.due_date }}</td><td>{{ money(Number(row.amount)) }}</td><td>{{ money(Number(row.outstanding)) }}</td><td>{{ row.status }}</td></tr></tbody></table><p v-if="!ledgers.receivables.length" class="users-empty">No outstanding revenue assessments.</p></div>
    </template>

    <template v-else-if="activeItem === 'accounts-payable'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Request</th><th>Payee</th><th>Date</th><th>Amount</th><th>Status</th></tr></thead><tbody><tr v-for="row in ledgers.payables" :key="String(row.name)"><td>{{ row.name }}</td><td>{{ row.party }}</td><td>{{ row.due_date }}</td><td>{{ money(Number(row.amount)) }}</td><td>{{ row.status }}</td></tr></tbody></table><p v-if="!ledgers.payables.length" class="users-empty">No approved or pending payment requests.</p></div>
    </template>

    <template v-else-if="activeItem === 'bank-reconciliation'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Bank accounts and mandates</h3></div><div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Account</th><th>Bank</th><th>Default</th><th>Status</th></tr></thead><tbody><tr v-for="row in banking.accounts" :key="String(row.name)"><td>{{ row.account_name }}</td><td>{{ row.bank }}</td><td>{{ row.is_default ? 'Yes' : 'No' }}</td><td>{{ row.disabled ? 'Disabled' : 'Active' }}</td></tr></tbody></table><p v-if="!banking.accounts.length" class="users-empty">No ERPNext bank accounts configured for this LGA.</p></div>
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Reconciliation queue</h3></div><div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Date</th><th>Bank account</th><th>Deposit</th><th>Withdrawal</th><th>Unallocated</th><th>Status</th></tr></thead><tbody><tr v-for="row in banking.transactions" :key="String(row.name)"><td>{{ row.date }}</td><td>{{ row.bank_account }}</td><td>{{ money(Number(row.deposit)) }}</td><td>{{ money(Number(row.withdrawal)) }}</td><td>{{ money(Number(row.unallocated_amount)) }}</td><td>{{ row.status }}</td></tr></tbody></table><p v-if="!banking.transactions.length" class="users-empty">No submitted bank transactions awaiting reconciliation.</p></div>
    </template>

    <template v-else-if="activeItem === 'trial-balance'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Trial balance</h3><label>Fiscal year<select v-model="trialBalanceFiscalYear"><option value="">All time</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
      <div class="staff-table-wrap" v-if="trialBalance"><table class="staff-table finance-table"><thead><tr><th>Account</th><th>Root type</th><th>Debit</th><th>Credit</th></tr></thead><tbody><tr v-for="row in trialBalance.rows" :key="row.account"><td>{{ row.account }}</td><td>{{ row.root_type }}</td><td>{{ money(row.debit) }}</td><td>{{ money(row.credit) }}</td></tr></tbody><tfoot><tr><td colspan="2"><strong>Total</strong></td><td><strong>{{ money(trialBalance.total_debit) }}</strong></td><td><strong>{{ money(trialBalance.total_credit) }}</strong></td></tr></tfoot></table><p v-if="!trialBalance.rows.length" class="users-empty">No ledger postings to report for this period.</p></div>
    </template>
  </template>
</template>
