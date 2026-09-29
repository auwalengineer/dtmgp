<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { AssetDisposalRecord, AssetMaintenanceRecord, AssetMovementRecord, AssetRecord, AssetVerificationRecord, Options } from "./types";

const props = defineProps<{ assets: AssetRecord[]; assetMovements: AssetMovementRecord[]; assetMaintenance: AssetMaintenanceRecord[]; assetVerifications: AssetVerificationRecord[]; assetDisposals: AssetDisposalRecord[]; options: Options; canManage: boolean }>();
const emit = defineEmits<{ "new-asset": []; "new-verification": []; "new-movement": [purpose: string]; "submit-asset": [name: string]; "new-disposal": [] }>();

const ITEM_LABELS: Record<string, string> = { "asset-register": "Asset Register", "asset-categories": "Asset Categories", "asset-locations": "Asset Locations", "asset-assignments": "Asset Assignments", "asset-transfers": "Asset Transfers", "asset-maintenance": "Asset Maintenance", "asset-disposal": "Asset Disposal", "asset-verification": "Asset Verification" };
const DEFAULT_ITEM = "asset-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const assignments = computed(() => props.assetMovements.filter((m) => ["Issue", "Receipt"].includes(m.purpose)));
const transfers = computed(() => props.assetMovements.filter((m) => ["Transfer", "Transfer and Issue"].includes(m.purpose)));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'asset-register'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Asset register</h3><button v-if="canManage" class="secondary-action" @click="emit('new-asset')"><FilePlus2 :size="15" /> New asset</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Asset</th><th>Category</th><th>Location</th><th>Status</th><th>Purchase amount</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in assets" :key="item.name" v-record="{ doctype: 'Asset', name: item.name }"><td><strong>{{ item.asset_name }}</strong><br /><small>{{ item.name }}</small></td><td>{{ item.asset_category }}</td><td>{{ item.location || '-' }}</td><td><span class="table-status" :class="item.docstatus === 1 ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.gross_purchase_amount.toLocaleString() }}</td><td v-if="canManage"><button v-if="item.docstatus === 0" class="secondary-action compact-action" @click="emit('submit-asset', item.name)">Submit</button></td></tr></tbody></table><p v-if="!assets.length" class="users-empty">No assets registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-categories'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Category</th></tr></thead><tbody><tr v-for="item in options.asset_categories" :key="item"><td><strong>{{ item }}</strong></td></tr></tbody></table><p v-if="!options.asset_categories.length" class="users-empty">No asset categories configured yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-locations'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Location</th><th>Coordinates</th></tr></thead><tbody><tr v-for="item in options.locations" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.latitude && item.longitude ? `${item.latitude}, ${item.longitude}` : 'Not geo-tagged' }}</td></tr></tbody></table><p v-if="!options.locations.length" class="users-empty">No locations configured yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-assignments'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Asset assignments</h3><button v-if="canManage" class="secondary-action" @click="emit('new-movement', 'Issue')"><FilePlus2 :size="15" /> New assignment</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Purpose</th><th>Date</th><th>Status</th></tr></thead><tbody><tr v-for="item in assignments" :key="item.name" v-record="{ doctype: 'Asset Movement', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.purpose }}</td><td>{{ item.transaction_date }}</td><td><span class="table-status" :class="item.docstatus === 1 ? 'success' : 'neutral'">{{ item.docstatus === 1 ? 'Submitted' : 'Draft' }}</span></td></tr></tbody></table><p v-if="!assignments.length" class="users-empty">No asset assignments recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-transfers'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Asset transfers</h3><button v-if="canManage" class="secondary-action" @click="emit('new-movement', 'Transfer')"><FilePlus2 :size="15" /> New transfer</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Purpose</th><th>Date</th><th>Status</th></tr></thead><tbody><tr v-for="item in transfers" :key="item.name" v-record="{ doctype: 'Asset Movement', name: item.name }"><td><strong>{{ item.name }}</strong></td><td>{{ item.purpose }}</td><td>{{ item.transaction_date }}</td><td><span class="table-status" :class="item.docstatus === 1 ? 'success' : 'neutral'">{{ item.docstatus === 1 ? 'Submitted' : 'Draft' }}</span></td></tr></tbody></table><p v-if="!transfers.length" class="users-empty">No asset transfers recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-maintenance'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Asset</th><th>Maintenance team</th></tr></thead><tbody><tr v-for="item in assetMaintenance" :key="item.name" v-record="{ doctype: 'Asset Maintenance', name: item.name }"><td><strong>{{ item.asset_name }}</strong></td><td>{{ item.maintenance_team || '-' }}</td></tr></tbody></table><p v-if="!assetMaintenance.length" class="users-empty">No maintenance schedules recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-disposal'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Asset disposal requests</h3><button v-if="canManage" class="secondary-action" @click="emit('new-disposal')"><FilePlus2 :size="15" /> New disposal request</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Asset</th><th>Method</th><th>Valuation</th><th>Status</th><th>Journal entry</th></tr></thead><tbody><tr v-for="item in assetDisposals" :key="item.name" v-record="{ doctype: 'DTMGP Asset Disposal', name: item.name }"><td><strong>{{ item.asset }}</strong></td><td>{{ item.disposal_method }}</td><td>{{ item.valuation_amount.toLocaleString() }}</td><td><span class="table-status" :class="item.status === 'Disposed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.journal_entry || 'Not posted yet' }}</td></tr></tbody></table><p v-if="!assetDisposals.length" class="users-empty">No asset disposal requests recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-verification'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Asset verification</h3><button v-if="canManage" class="secondary-action" @click="emit('new-verification')"><FilePlus2 :size="15" /> New verification</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Asset</th><th>Verification date</th><th>Verified by</th><th>Condition</th></tr></thead><tbody><tr v-for="item in assetVerifications" :key="item.name" v-record="{ doctype: 'DTMGP Asset Verification', name: item.name }"><td><strong>{{ item.asset }}</strong></td><td>{{ item.verification_date }}</td><td>{{ item.verified_by || '-' }}</td><td><span class="table-status" :class="item.condition === 'Good' ? 'success' : 'neutral'">{{ item.condition }}</span></td></tr></tbody></table><p v-if="!assetVerifications.length" class="users-empty">No asset verification records for this LGA.</p></div>
  </template>
</template>
