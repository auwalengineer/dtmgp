<script setup lang="ts">
import { FileStack } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { Contractor, ContractorPerformance } from "./types";

const props = defineProps<{ contractors: Contractor[]; performance: ContractorPerformance[]; canManage: boolean }>();
const emit = defineEmits<{ "set-hold": [supplier: string, onHold: boolean] }>();

const ITEM_LABELS: Record<string, string> = { "contractor-register": "Contractor Register", "contractor-documents": "Contractor Documents", "contractor-performance": "Contractor Performance", "blacklisted-contractors": "Blacklisted Contractors" };
const DEFAULT_ITEM = "contractor-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const blacklisted = computed(() => props.contractors.filter((c) => c.disabled || c.on_hold));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'contractor-register'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contractor</th><th>Type</th><th>Group</th><th>Status</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in contractors" :key="item.name" v-record="{ doctype: 'Supplier', name: item.name }"><td><strong>{{ item.supplier_name }}</strong></td><td>{{ item.supplier_type }}</td><td>{{ item.supplier_group || '-' }}</td><td><span class="table-status" :class="!item.disabled && !item.on_hold ? 'success' : 'neutral'">{{ item.disabled ? 'Blacklisted' : item.on_hold ? 'On hold' : 'Active' }}</span></td><td v-if="canManage"><button v-if="!item.disabled && !item.on_hold" class="secondary-action compact-action" @click="emit('set-hold', item.name, true)">Put on hold</button><button v-else class="secondary-action compact-action" @click="emit('set-hold', item.name, false)">Restore</button></td></tr></tbody></table><p v-if="!contractors.length" class="users-empty">No contractors registered yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'contractor-documents'">
    <PreviewCard :icon="FileStack" title="Contractor documents" body="Storage of contractor registration certificates, tax clearance and other compliance documents isn't available yet -- this class of record also awaits the same records/legal retention sign-off noted for HR personnel files." />
  </template>

  <template v-else-if="activeItem === 'contractor-performance'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contractor</th><th>Cases</th><th>Completed</th><th>Estimated total</th><th>Evaluated total</th></tr></thead><tbody><tr v-for="item in performance" :key="item.supplier" v-record="{ doctype: 'Supplier', name: item.supplier }"><td><strong>{{ item.supplier }}</strong></td><td>{{ item.cases }}</td><td>{{ item.completed }}</td><td>{{ item.estimated_total.toLocaleString() }}</td><td>{{ item.evaluated_total.toLocaleString() }}</td></tr></tbody></table><p v-if="!performance.length" class="users-empty">No completed procurement cases to derive performance from yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'blacklisted-contractors'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contractor</th><th>Hold type</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in blacklisted" :key="item.name" v-record="{ doctype: 'Supplier', name: item.name }"><td><strong>{{ item.supplier_name }}</strong></td><td>{{ item.disabled ? 'Blacklisted' : item.hold_type || 'On hold' }}</td><td v-if="canManage"><button class="secondary-action compact-action" @click="emit('set-hold', item.name, false)">Restore</button></td></tr></tbody></table><p v-if="!blacklisted.length" class="users-empty">No blacklisted or on-hold contractors.</p></div>
  </template>
</template>
