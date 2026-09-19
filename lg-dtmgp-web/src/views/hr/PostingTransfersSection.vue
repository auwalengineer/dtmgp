<script setup lang="ts">
import { ArrowLeftRight, UserCheck } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { docstatusLabel } from "./types";
import type { Transfer } from "./types";

const props = defineProps<{ transfers: Transfer[]; canManage: boolean }>();
defineEmits<{ "new-movement": []; "submit-transfer": [name: string]; "cancel-transfer": [name: string] }>();

const ITEM_LABELS: Record<string, string> = { "posting-requests": "Posting Requests", "transfer-requests": "Transfer Requests", "posting-orders": "Posting Orders", "transfer-orders": "Transfer Orders", "posting-history": "Posting History", "transfer-history": "Transfer History", "assumption-of-duty": "Assumption of Duty" };
const DEFAULT_ITEM = "posting-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

function destination(transfer: Transfer) { return transfer.movement_type === "Transfer" ? transfer.new_company : transfer.department; }
const postingRequests = computed(() => props.transfers.filter((t) => t.movement_type === "Posting" && t.docstatus === 0));
const transferRequests = computed(() => props.transfers.filter((t) => t.movement_type === "Transfer" && t.docstatus === 0));
const postingOrders = computed(() => props.transfers.filter((t) => t.movement_type === "Posting" && t.docstatus === 1));
const transferOrders = computed(() => props.transfers.filter((t) => t.movement_type === "Transfer" && t.docstatus === 1));
const postingHistory = computed(() => props.transfers.filter((t) => t.movement_type === "Posting"));
const transferHistory = computed(() => props.transfers.filter((t) => t.movement_type === "Transfer"));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <div class="directory-toolbar"><h3 style="margin:0;flex:1">{{ ITEM_LABELS[activeItem] }}</h3><button v-if="canManage && activeItem !== 'assumption-of-duty'" class="secondary-action" @click="$emit('new-movement')"><ArrowLeftRight :size="15" /> New movement</button></div>

  <template v-if="activeItem === 'posting-requests'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th></th></tr></thead><tbody><tr v-for="transfer in postingRequests" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('submit-transfer', transfer.name)">Submit</button></td></tr></tbody></table><p v-if="!postingRequests.length" class="users-empty">No posting requests awaiting submission.</p></div>
  </template>
  <template v-else-if="activeItem === 'transfer-requests'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th></th></tr></thead><tbody><tr v-for="transfer in transferRequests" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('submit-transfer', transfer.name)">Submit</button></td></tr></tbody></table><p v-if="!transferRequests.length" class="users-empty">No transfer requests awaiting submission.</p></div>
  </template>
  <template v-else-if="activeItem === 'posting-orders'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th></th></tr></thead><tbody><tr v-for="transfer in postingOrders" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('cancel-transfer', transfer.name)">Cancel</button></td></tr></tbody></table><p v-if="!postingOrders.length" class="users-empty">No issued posting orders.</p></div>
  </template>
  <template v-else-if="activeItem === 'transfer-orders'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th></th></tr></thead><tbody><tr v-for="transfer in transferOrders" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('cancel-transfer', transfer.name)">Cancel</button></td></tr></tbody></table><p v-if="!transferOrders.length" class="users-empty">No issued transfer orders.</p></div>
  </template>
  <template v-else-if="activeItem === 'posting-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th>Status</th></tr></thead><tbody><tr v-for="transfer in postingHistory" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><span class="table-status" :class="transfer.docstatus === 1 ? 'success' : 'neutral'">{{ docstatusLabel(transfer.docstatus) }}</span></td></tr></tbody></table><p v-if="!postingHistory.length" class="users-empty">No posting history for this LGA.</p></div>
  </template>
  <template v-else-if="activeItem === 'transfer-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Destination</th><th>Effective</th><th>Status</th></tr></thead><tbody><tr v-for="transfer in transferHistory" :key="transfer.name"><td>{{ transfer.employee_name }}</td><td>{{ destination(transfer) }}</td><td>{{ transfer.transfer_date }}</td><td><span class="table-status" :class="transfer.docstatus === 1 ? 'success' : 'neutral'">{{ docstatusLabel(transfer.docstatus) }}</span></td></tr></tbody></table><p v-if="!transferHistory.length" class="users-empty">No transfer history for this LGA.</p></div>
  </template>
  <template v-else-if="activeItem === 'assumption-of-duty'">
    <PreviewCard :icon="UserCheck" title="Assumption of duty" body="Confirming that a transferred or posted staff member has resumed duty at their destination isn't tracked yet — postings and transfers stop at order issuance today." />
  </template>
</template>
