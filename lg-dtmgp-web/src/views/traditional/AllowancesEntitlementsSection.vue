<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Allowance, Ruler } from "./types";
import { ALLOWANCE_CHAIN, money, nextInChain, today } from "./types";

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "entitlement-register": "Entitlement Register", "allowance-processing": "Allowance Processing", "payment-history": "Payment History" };
const DEFAULT_ITEM = "entitlement-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const allowances = ref<Allowance[]>([]);
const rulers = ref<Ruler[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [allowances.value, rulers.value] = await Promise.all([
      apiRequest<{ items: Allowance[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Allowance")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: Ruler[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Ruler")}&company=${company}&page_size=100`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load allowances"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAll, { immediate: true });

const processing = computed(() => allowances.value.filter((a) => ["Draft", "Approved"].includes(a.status)));
const paymentHistory = computed(() => allowances.value.filter((a) => a.status === "Paid"));

async function advance(name: string) {
  const record = allowances.value.find((a) => a.name === name);
  const target = record && nextInChain(ALLOWANCE_CHAIN, record.status);
  if (!target) return;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Allowance", name, target_status: target }) });
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the allowance"; }
}

function rulerName(name: string) { return rulers.value.find((r) => r.name === name)?.ruler_name || name; }

const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string | number>>({});
function openCreate() { form.value = { ruler: "", allowance_type: "Stipend", amount: 0, period_start: today(), period_end: today() }; showForm.value = true; }
async function saveAllowance() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Traditional Allowance", values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the allowance"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>

  <template v-if="activeItem === 'entitlement-register'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Entitlement register</h3><button v-if="canManage" class="secondary-action" @click="openCreate"><FilePlus2 :size="15" /> New allowance</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Type</th><th>Amount</th><th>Period</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in allowances" :key="item.name"><td><strong>{{ rulerName(item.ruler) }}</strong></td><td>{{ item.allowance_type }}</td><td>{{ money(item.amount) }}</td><td>{{ item.period_start }} – {{ item.period_end }}</td><td><span class="table-status" :class="item.status === 'Paid' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && nextInChain(ALLOWANCE_CHAIN, item.status)" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading...</p><p v-else-if="!allowances.length" class="users-empty">No allowances recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'allowance-processing'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Type</th><th>Amount</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in processing" :key="item.name"><td><strong>{{ rulerName(item.ruler) }}</strong></td><td>{{ item.allowance_type }}</td><td>{{ money(item.amount) }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="!processing.length" class="users-empty">No allowances awaiting processing.</p></div>
  </template>

  <template v-else-if="activeItem === 'payment-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Ruler</th><th>Type</th><th>Amount</th><th>Paid</th></tr></thead><tbody><tr v-for="item in paymentHistory" :key="item.name"><td><strong>{{ rulerName(item.ruler) }}</strong></td><td>{{ item.allowance_type }}</td><td>{{ money(item.amount) }}</td><td>{{ item.payment_date }}</td></tr></tbody></table><p v-if="!paymentHistory.length" class="users-empty">No allowance payments recorded yet.</p></div>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveAllowance"><h2>New allowance</h2><div class="form-grid">
    <label>Ruler<select v-model="form.ruler" required><option value="" disabled>Select ruler</option><option v-for="item in rulers" :key="item.name" :value="item.name">{{ item.ruler_name }}</option></select></label>
    <label>Type<select v-model="form.allowance_type"><option>Stipend</option><option>Security</option><option>Vehicle</option><option>Palace Maintenance</option><option>Sitting Allowance</option></select></label>
    <label>Amount<input v-model.number="form.amount" type="number" min="0.01" step="0.01" required /></label>
    <label>Period start<input v-model="form.period_start" type="date" required /></label>
    <label>Period end<input v-model="form.period_end" type="date" required /></label>
  </div><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save allowance" }}</button></footer></form></div>
</template>
