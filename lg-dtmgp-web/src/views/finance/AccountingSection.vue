<script setup lang="ts">
import { BookOpenText, Landmark, ListTree, Scale, ScrollText, Wallet, WalletCards } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "chart-of-accounts": "Chart of Accounts", "journal-entries": "Journal Entries", "general-ledger": "General Ledger", "accounts-receivable": "Accounts Receivable", "accounts-payable": "Accounts Payable", "bank-reconciliation": "Bank Reconciliation", "trial-balance": "Trial Balance" };
const DEFAULT_ITEM = "chart-of-accounts";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'chart-of-accounts'">
    <PreviewCard :icon="ListTree" title="Chart of accounts" body="A dedicated chart-of-accounts view isn't available yet — ERPNext's Account list already exists and feeds the account pickers on Procurement and Payment forms, but there is no read view here yet." />
  </template>
  <template v-else-if="activeItem === 'journal-entries'">
    <PreviewCard :icon="ScrollText" title="Journal entries" body="A journal entry list/view isn't available yet — this maps to ERPNext's native Journal Entry doctype, which isn't exposed through the finance API." />
  </template>
  <template v-else-if="activeItem === 'general-ledger'">
    <PreviewCard :icon="BookOpenText" title="General ledger" body="A general ledger view isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'accounts-receivable'">
    <PreviewCard :icon="Wallet" title="Accounts receivable" body="An accounts receivable view isn't available yet — outstanding revenue assessments are visible under Revenue Performance in the meantime." />
  </template>
  <template v-else-if="activeItem === 'accounts-payable'">
    <PreviewCard :icon="WalletCards" title="Accounts payable" body="An accounts payable view isn't available yet — pending payment requests are visible under Expenditure in the meantime." />
  </template>
  <template v-else-if="activeItem === 'bank-reconciliation'">
    <PreviewCard :icon="Landmark" title="Bank reconciliation" body="Bank reconciliation isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'trial-balance'">
    <PreviewCard :icon="Scale" title="Trial balance" body="A trial balance report isn't available yet." />
  </template>
</template>
