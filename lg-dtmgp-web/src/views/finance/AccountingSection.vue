<script setup lang="ts">
import { Landmark, Scale, Wallet, WalletCards } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
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
      <PreviewCard :icon="Wallet" title="Accounts receivable" body="A dedicated accounts-receivable ledger isn't available yet -- outstanding revenue assessments are visible under Revenue Performance in the meantime." />
    </template>

    <template v-else-if="activeItem === 'accounts-payable'">
      <PreviewCard :icon="WalletCards" title="Accounts payable" body="A dedicated accounts-payable ledger isn't available yet -- pending payment requests are visible under Expenditure in the meantime." />
    </template>

    <template v-else-if="activeItem === 'bank-reconciliation'">
      <PreviewCard :icon="Landmark" title="Bank reconciliation" body="Bank reconciliation isn't available yet -- it depends on approved bank signatories and Bank Account setup (see docs/implementation-status.md's external production conditions)." />
    </template>

    <template v-else-if="activeItem === 'trial-balance'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Trial balance</h3><label>Fiscal year<select v-model="trialBalanceFiscalYear"><option value="">All time</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label></div>
      <div class="staff-table-wrap" v-if="trialBalance"><table class="staff-table finance-table"><thead><tr><th>Account</th><th>Root type</th><th>Debit</th><th>Credit</th></tr></thead><tbody><tr v-for="row in trialBalance.rows" :key="row.account"><td>{{ row.account }}</td><td>{{ row.root_type }}</td><td>{{ money(row.debit) }}</td><td>{{ money(row.credit) }}</td></tr></tbody><tfoot><tr><td colspan="2"><strong>Total</strong></td><td><strong>{{ money(trialBalance.total_debit) }}</strong></td><td><strong>{{ money(trialBalance.total_credit) }}</strong></td></tr></tfoot></table><p v-if="!trialBalance.rows.length" class="users-empty">No ledger postings to report for this period.</p></div>
    </template>
  </template>
</template>
