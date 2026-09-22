<script setup lang="ts">
import { FilePlus2, HandCoins, Plus, Trash2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import { money, today } from "./types";
import type { Allocation, AllocationDistribution } from "./types";

const props = defineProps<{ canManage: boolean; fiscalYears: string[]; departments: string[] }>();
const session = useSessionStore();

const NEXT_STATUS: Record<string, string> = { Expected: "Received", Received: "Distributed" };
const ITEM_LABELS: Record<string, string> = { "allocation-register": "Allocation Register", "allocation-receipts": "Allocation Receipts", "allocation-distribution": "Allocation Distribution", "allocation-utilization": "Allocation Utilization" };
const DEFAULT_ITEM = "allocation-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const loading = ref(true);
const error = ref("");
const allocations = ref<Allocation[]>([]);
const distributions = ref<AllocationDistribution[]>([]);

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function load() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    [allocations.value, distributions.value] = await Promise.all([
      apiRequest<{ items: Allocation[] }>(`/api/method/dtmgp.api.v1.finance.list_allocations?${scopeQuery()}`).then((r) => r.items),
      apiRequest<{ items: AllocationDistribution[] }>(`/api/method/dtmgp.api.v1.finance.get_allocation_distributions?${scopeQuery()}`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load allocations"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, load, { immediate: true });

const receivedAllocations = computed(() => allocations.value.filter((a) => a.status !== "Expected"));
const distributableAllocations = computed(() => allocations.value.filter((a) => a.status === "Received"));

async function advance(name: string, target: string) {
  error.value = "";
  try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Allocation", name, target_status: target }) }); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the allocation"; }
}

const showNewForm = ref(false);
const newForm = ref({ fiscal_year: "", tier: "Federal Allocation", source: "", tranche_period: "", amount: 0, expected_date: today() });
const saving = ref(false);
async function createAllocation() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Allocation", values: { ...newForm.value, company: session.activeLga } }) });
    showNewForm.value = false;
    newForm.value = { fiscal_year: "", tier: "Federal Allocation", source: "", tranche_period: "", amount: 0, expected_date: today() };
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to create the allocation"; }
  finally { saving.value = false; }
}

const distributeTarget = ref<Allocation | null>(null);
const distributeRows = ref<{ department: string; purpose: string; amount: number }[]>([]);
function openDistribute(allocation: Allocation) {
  distributeTarget.value = allocation;
  distributeRows.value = [
    ...distributions.value.filter((d) => d.allocation === allocation.name).map((d) => ({ department: d.department, purpose: d.purpose, amount: d.amount })),
    { department: "", purpose: "", amount: 0 },
  ];
}
function addDistributionRow() { distributeRows.value.push({ department: "", purpose: "", amount: 0 }); }
function removeDistributionRow(index: number) { distributeRows.value.splice(index, 1); }
async function saveDistribution() {
  if (!distributeTarget.value) return;
  saving.value = true;
  error.value = "";
  try {
    const rows = distributeRows.value.filter((row) => row.department && row.amount > 0);
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Allocation", name: distributeTarget.value.name, values: { distributions: rows } }) });
    distributeTarget.value = null;
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the distribution"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading allocations...</p>

  <template v-else>
    <template v-if="activeItem === 'allocation-register'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Allocation register</h3><button v-if="canManage" class="secondary-action" @click="showNewForm = true"><FilePlus2 :size="15" /> New allocation</button></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Tier</th><th>Source</th><th>Tranche</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in allocations" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.tier }}</td><td>{{ item.source }}</td><td>{{ item.tranche_period }}</td><td>{{ money(item.amount) }}</td><td><span class="table-status" :class="item.status === 'Distributed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="advance(item.name, NEXT_STATUS[item.status])">Advance to {{ NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!allocations.length" class="users-empty">No allocations recorded for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'allocation-receipts'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Reference</th><th>Tranche</th><th>Amount</th><th>Received</th><th>Bank reference</th></tr></thead><tbody><tr v-for="item in receivedAllocations" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.tranche_period }}</td><td>{{ money(item.amount) }}</td><td>{{ item.received_date || '-' }}</td><td>{{ item.bank_reference || '-' }}</td></tr></tbody></table><p v-if="!receivedAllocations.length" class="users-empty">No allocations have been received yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'allocation-distribution'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Allocation distribution</h3></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Allocation</th><th>Department</th><th>Purpose</th><th>Amount</th></tr></thead><tbody><tr v-for="row in distributions" :key="row.name"><td><strong>{{ row.allocation }}</strong></td><td>{{ row.department }}</td><td>{{ row.purpose || '-' }}</td><td>{{ money(row.amount) }}</td></tr></tbody></table><p v-if="!distributions.length" class="users-empty">No allocations have been distributed across departments yet.</p></div>
      <div class="staff-table-wrap" v-if="canManage && distributableAllocations.length"><table class="staff-table finance-table"><thead><tr><th>Received allocations awaiting distribution</th><th></th></tr></thead><tbody><tr v-for="item in distributableAllocations" :key="item.name"><td>{{ item.name }} — {{ item.tranche_period }} ({{ money(item.amount - item.distributed_total) }} remaining)</td><td><button class="secondary-action compact-action" @click="openDistribute(item)"><HandCoins :size="14" /> Distribute</button></td></tr></tbody></table></div>
    </template>

    <template v-else-if="activeItem === 'allocation-utilization'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Allocation</th><th>Amount</th><th>Distributed</th><th>Utilization</th></tr></thead><tbody><tr v-for="item in allocations" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ money(item.amount) }}</td><td>{{ money(item.distributed_total) }}</td><td>{{ item.amount ? Math.round((item.distributed_total / item.amount) * 100) : 0 }}%</td></tr></tbody></table><p v-if="!allocations.length" class="users-empty">No allocations to report utilization for yet.</p></div>
    </template>
  </template>

  <div v-if="showNewForm" class="modal-backdrop" @click.self="showNewForm = false"><form class="user-modal finance-modal" @submit.prevent="createAllocation">
    <h2>New allocation</h2>
    <div class="form-grid">
      <label>Fiscal year<select v-model="newForm.fiscal_year" required><option value="" disabled>Select year</option><option v-for="year in fiscalYears" :key="year">{{ year }}</option></select></label>
      <label>Tier<select v-model="newForm.tier"><option>Federal Allocation</option><option>State Allocation</option><option>Internally Generated Support</option><option>Other</option></select></label>
      <label>Source<input v-model="newForm.source" required placeholder="e.g. Federal Account Allocation Committee" /></label>
      <label>Tranche period<input v-model="newForm.tranche_period" required placeholder="e.g. September 2026" /></label>
      <label>Amount<input v-model.number="newForm.amount" type="number" min="0.01" step="0.01" required /></label>
      <label>Expected date<input v-model="newForm.expected_date" type="date" /></label>
    </div>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showNewForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save allocation" }}</button></footer>
  </form></div>

  <div v-if="distributeTarget" class="modal-backdrop" @click.self="distributeTarget = null"><form class="user-modal finance-modal" @submit.prevent="saveDistribution">
    <h2>Distribute {{ distributeTarget.name }}</h2>
    <p class="users-empty" style="text-align:left;padding:0">{{ money(distributeTarget.amount) }} total for {{ distributeTarget.tranche_period }}.</p>
    <div v-for="(row, index) in distributeRows" :key="index" class="form-grid" style="border-bottom:1px solid var(--border-color, #e5e5e5);padding-bottom:8px;margin-bottom:8px">
      <label>Department<select v-model="row.department" required><option value="" disabled>Select department</option><option v-for="dept in departments" :key="dept">{{ dept }}</option></select></label>
      <label>Purpose<input v-model="row.purpose" /></label>
      <label>Amount<input v-model.number="row.amount" type="number" min="0" step="0.01" /></label>
      <button type="button" class="secondary-action compact-action" @click="removeDistributionRow(index)"><Trash2 :size="14" /> Remove</button>
    </div>
    <button type="button" class="secondary-action compact-action" @click="addDistributionRow"><Plus :size="14" /> Add row</button>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="distributeTarget = null">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save distribution" }}</button></footer>
  </form></div>
</template>
