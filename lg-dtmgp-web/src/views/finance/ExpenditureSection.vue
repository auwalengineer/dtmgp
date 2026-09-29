<script setup lang="ts">
import { FilePlus2, Receipt } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money } from "./types";
import type { PaymentRequest } from "./types";

const props = defineProps<{ paymentRequests: PaymentRequest[]; canManage: boolean }>();
defineEmits<{ "new-payment-request": []; "advance-payment": [name: string, target: string] }>();

const NEXT_STATUS: Record<string, string> = { Draft: "Budget Checked", "Budget Checked": "Pending Audit", "Pending Audit": "Pending Approval", "Pending Approval": "Approved" };
const ITEM_LABELS: Record<string, string> = { "payment-requests": "Payment Requests", "expense-claims": "Expense Claims", "expenditure-approvals": "Expenditure Approvals", "payment-vouchers": "Payment Vouchers", "expenditure-register": "Expenditure Register" };
const DEFAULT_ITEM = "payment-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const pendingApproval = computed(() => props.paymentRequests.filter((p) => ["Budget Checked", "Pending Audit", "Pending Approval"].includes(p.status)));
const paidRequests = computed(() => props.paymentRequests.filter((p) => p.status === "Paid"));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'payment-requests'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Payment requests</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-payment-request')"><FilePlus2 :size="15" /> New payment request</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Payee</th><th>Description</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in paymentRequests" :key="item.name" v-record="{ doctype: 'DTMGP Payment Request', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.payee }}</td><td>{{ item.description }}</td><td>{{ money(item.amount) }}</td><td><span class="table-status" :class="item.status === 'Paid' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="$emit('advance-payment', item.name, NEXT_STATUS[item.status])">Advance to {{ NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!paymentRequests.length" class="users-empty">No payment requests recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'expense-claims'">
    <PreviewCard :icon="Receipt" title="Expense claims" body="Employee expense claims aren't exposed yet — this maps to ERPNext's native Expense Claim doctype, which isn't wired into the finance API." />
  </template>

  <template v-else-if="activeItem === 'expenditure-approvals'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Payee</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in pendingApproval" :key="item.name" v-record="{ doctype: 'DTMGP Payment Request', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.payee }}</td><td>{{ money(item.amount) }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage && NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="$emit('advance-payment', item.name, NEXT_STATUS[item.status])">Advance to {{ NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!pendingApproval.length" class="users-empty">No payment requests awaiting approval.</p></div>
  </template>

  <template v-else-if="activeItem === 'payment-vouchers'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Payee</th><th>Amount</th><th>Payment entry</th></tr></thead><tbody><tr v-for="item in paidRequests" :key="item.name" v-record="{ doctype: 'DTMGP Payment Request', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.payee }}</td><td>{{ money(item.amount) }}</td><td>{{ item.payment_entry || '-' }}</td></tr></tbody></table><p v-if="!paidRequests.length" class="users-empty">No paid requests with a linked payment voucher yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'expenditure-register'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Payee</th><th>Amount</th><th>Status</th></tr></thead><tbody><tr v-for="item in paymentRequests" :key="item.name" v-record="{ doctype: 'DTMGP Payment Request', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.payee }}</td><td>{{ money(item.amount) }}</td><td><span class="table-status" :class="item.status === 'Paid' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="!paymentRequests.length" class="users-empty">No expenditure recorded for this LGA.</p></div>
  </template>
</template>
