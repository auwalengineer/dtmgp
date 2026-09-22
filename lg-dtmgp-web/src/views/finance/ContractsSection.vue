<script setup lang="ts">
import { FilePlus2, Plus, Trash2, Users } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money, today } from "./types";
import type { Contract, ContractMilestone, ContractVariation, ProcurementCase } from "./types";

const props = defineProps<{ canManage: boolean }>();
const session = useSessionStore();

const CONTRACT_NEXT_STATUS: Record<string, string> = { Draft: "Active", Active: "Completed" };
const VARIATION_NEXT_STATUS: Record<string, string> = { Draft: "Pending Approval", "Pending Approval": "Approved" };
const ITEM_LABELS: Record<string, string> = { "contract-register": "Contract Register", "contractor-profiles": "Contractor Profiles", "contract-milestones": "Contract Milestones", "certificates-payments": "Certificates & Payments", "contract-variations": "Contract Variations", "contract-completion": "Contract Completion" };
const DEFAULT_ITEM = "contract-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const loading = ref(true);
const error = ref("");
const contracts = ref<Contract[]>([]);
const milestones = ref<ContractMilestone[]>([]);
const variations = ref<ContractVariation[]>([]);
const eligibleCases = ref<ProcurementCase[]>([]);
const contractors = ref<{ name: string; supplier_name: string }[]>([]);

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function load() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    [contracts.value, milestones.value, variations.value, eligibleCases.value, contractors.value] = await Promise.all([
      apiRequest<{ items: Contract[] }>(`/api/method/dtmgp.api.v1.finance.list_records?doctype=DTMGP%20Contract&${scopeQuery()}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: ContractMilestone[] }>(`/api/method/dtmgp.api.v1.finance.get_contract_milestones?${scopeQuery()}`).then((r) => r.items),
      apiRequest<{ items: ContractVariation[] }>(`/api/method/dtmgp.api.v1.finance.list_records?doctype=DTMGP%20Contract%20Variation&${scopeQuery()}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: ProcurementCase[] }>(`/api/method/dtmgp.api.v1.finance.list_records?doctype=DTMGP%20Procurement%20Case&${scopeQuery()}&page_size=100`).then((r) => r.items.filter((c) => ["Awarded", "Completed"].includes(c.status))),
      apiRequest<{ items: { name: string; supplier_name: string }[] }>("/api/method/dtmgp.api.v1.projects.list_contractors?page_size=100").then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load contracts"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, load, { immediate: true });

const certifiedMilestones = computed(() => milestones.value.filter((m) => m.status !== "Pending"));
const completedContracts = computed(() => contracts.value.filter((c) => c.status === "Completed"));

const saving = ref(false);
async function advanceContract(name: string, target: string) {
  error.value = "";
  try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Contract", name, target_status: target }) }); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the contract"; }
}
async function advanceVariation(name: string, target: string) {
  error.value = "";
  try { await apiRequest("/api/method/dtmgp.api.v1.finance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Contract Variation", name, target_status: target }) }); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the variation"; }
}

const showContractForm = ref(false);
const contractForm = ref({ title: "", procurement_case: "", contractor: "", contract_value: 0, start_date: today(), end_date: "" });
async function createContract() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Contract", values: { ...contractForm.value, company: session.activeLga } }) });
    showContractForm.value = false;
    contractForm.value = { title: "", procurement_case: "", contractor: "", contract_value: 0, start_date: today(), end_date: "" };
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to create the contract"; }
  finally { saving.value = false; }
}

const showVariationForm = ref(false);
const variationForm = ref({ contract: "", variation_type: "Cost Variation", amount_change: 0, days_change: 0, description: "" });
async function createVariation() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Contract Variation", values: { ...variationForm.value, company: session.activeLga } }) });
    showVariationForm.value = false;
    variationForm.value = { contract: "", variation_type: "Cost Variation", amount_change: 0, days_change: 0, description: "" };
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to create the variation"; }
  finally { saving.value = false; }
}

const milestoneTarget = ref<Contract | null>(null);
const milestoneRows = ref<{ title: string; due_date: string; amount: number }[]>([]);
function openMilestoneForm(contract: Contract) {
  milestoneTarget.value = contract;
  milestoneRows.value = [
    ...milestones.value.filter((m) => m.contract === contract.name).map((m) => ({ title: m.title, due_date: m.due_date || "", amount: m.amount })),
    { title: "", due_date: today(), amount: 0 },
  ];
}
function addMilestoneRow() { milestoneRows.value.push({ title: "", due_date: today(), amount: 0 }); }
function removeMilestoneRow(index: number) { milestoneRows.value.splice(index, 1); }
async function saveMilestones() {
  if (!milestoneTarget.value) return;
  saving.value = true;
  error.value = "";
  try {
    const rows = milestoneRows.value.filter((row) => row.title && row.amount > 0);
    await apiRequest("/api/method/dtmgp.api.v1.finance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Contract", name: milestoneTarget.value.name, values: { milestones: rows } }) });
    milestoneTarget.value = null;
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the milestones"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading contracts...</p>

  <template v-else>
    <template v-if="activeItem === 'contract-register'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Contract register</h3><button v-if="canManage && eligibleCases.length" class="secondary-action" @click="showContractForm = true"><FilePlus2 :size="15" /> New contract</button></div>
      <p v-if="canManage && !eligibleCases.length" class="users-empty" style="text-align:left;padding:0 20px">No Awarded or Completed procurement cases are available to contract against yet.</p>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contract</th><th>Contractor</th><th>Value</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in contracts" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.contractor }}</td><td>{{ money(item.contract_value) }}</td><td><span class="table-status" :class="item.status === 'Completed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && CONTRACT_NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="advanceContract(item.name, CONTRACT_NEXT_STATUS[item.status])">Advance to {{ CONTRACT_NEXT_STATUS[item.status] }}</button> <button v-if="canManage" class="secondary-action compact-action" @click="openMilestoneForm(item)">Milestones</button></td></tr></tbody></table><p v-if="!contracts.length" class="users-empty">No contracts recorded for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'contractor-profiles'">
      <PreviewCard :icon="Users" title="Contractor profiles" body="Contractor performance history and blacklist status are tracked in Projects, Assets & Field Monitoring's Contractor Register rather than duplicated here." />
    </template>

    <template v-else-if="activeItem === 'contract-milestones'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contract</th><th>Milestone</th><th>Due</th><th>Amount</th><th>Status</th></tr></thead><tbody><tr v-for="row in milestones" :key="row.name"><td>{{ row.contract }}</td><td><strong>{{ row.title }}</strong></td><td>{{ row.due_date || '-' }}</td><td>{{ money(row.amount) }}</td><td><span class="table-status" :class="row.status === 'Paid' ? 'success' : 'neutral'">{{ row.status }}</span></td></tr></tbody></table><p v-if="!milestones.length" class="users-empty">No contract milestones recorded yet -- add them from a contract's "Milestones" action in the Contract Register.</p></div>
    </template>

    <template v-else-if="activeItem === 'certificates-payments'">
      <p class="users-empty" style="text-align:left;padding:0 20px">Milestone certification and payment linkage are recorded directly in Frappe Desk for now -- this view lists milestones already marked Certified or Paid there.</p>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contract</th><th>Milestone</th><th>Amount</th><th>Certified</th><th>Payment request</th></tr></thead><tbody><tr v-for="row in certifiedMilestones" :key="row.name"><td>{{ row.contract }}</td><td>{{ row.title }}</td><td>{{ money(row.amount) }}</td><td>{{ row.certified_date || '-' }}</td><td>{{ row.payment_request || '-' }}</td></tr></tbody></table><p v-if="!certifiedMilestones.length" class="users-empty">No milestones have been certified yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'contract-variations'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Contract variations</h3><button v-if="canManage && contracts.length" class="secondary-action" @click="showVariationForm = true"><FilePlus2 :size="15" /> New variation</button></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contract</th><th>Type</th><th>Amount change</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in variations" :key="item.name"><td>{{ item.contract }}</td><td>{{ item.variation_type }}</td><td>{{ money(item.amount_change) }}</td><td><span class="table-status" :class="item.status === 'Approved' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && VARIATION_NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="advanceVariation(item.name, VARIATION_NEXT_STATUS[item.status])">Advance to {{ VARIATION_NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!variations.length" class="users-empty">No contract variations recorded yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'contract-completion'">
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Contract</th><th>Contractor</th><th>Value</th><th>Completion certificate</th></tr></thead><tbody><tr v-for="item in completedContracts" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.contractor }}</td><td>{{ money(item.contract_value) }}</td><td>{{ item.completion_certificate_reference || '-' }}</td></tr></tbody></table><p v-if="!completedContracts.length" class="users-empty">No contracts have reached completion yet.</p></div>
    </template>
  </template>

  <div v-if="showContractForm" class="modal-backdrop" @click.self="showContractForm = false"><form class="user-modal finance-modal" @submit.prevent="createContract">
    <h2>New contract</h2>
    <div class="form-grid">
      <label>Title<input v-model="contractForm.title" required /></label>
      <label>Procurement case<select v-model="contractForm.procurement_case" required><option value="" disabled>Select case</option><option v-for="item in eligibleCases" :key="item.name" :value="item.name">{{ item.title }}</option></select></label>
      <label>Contractor<select v-model="contractForm.contractor" required><option value="" disabled>Select contractor</option><option v-for="item in contractors" :key="item.name" :value="item.name">{{ item.supplier_name }}</option></select></label>
      <label>Contract value<input v-model.number="contractForm.contract_value" type="number" min="0.01" step="0.01" required /></label>
      <label>Start date<input v-model="contractForm.start_date" type="date" required /></label>
      <label>End date<input v-model="contractForm.end_date" type="date" /></label>
    </div>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showContractForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save contract" }}</button></footer>
  </form></div>

  <div v-if="showVariationForm" class="modal-backdrop" @click.self="showVariationForm = false"><form class="user-modal finance-modal" @submit.prevent="createVariation">
    <h2>New contract variation</h2>
    <div class="form-grid">
      <label>Contract<select v-model="variationForm.contract" required><option value="" disabled>Select contract</option><option v-for="item in contracts" :key="item.name" :value="item.name">{{ item.title }}</option></select></label>
      <label>Type<select v-model="variationForm.variation_type"><option>Time Extension</option><option>Cost Variation</option><option>Scope Change</option></select></label>
      <label>Amount change<input v-model.number="variationForm.amount_change" type="number" step="0.01" /></label>
      <label>Days change<input v-model.number="variationForm.days_change" type="number" /></label>
      <label class="full-field">Description<textarea v-model="variationForm.description" required></textarea></label>
    </div>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showVariationForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save variation" }}</button></footer>
  </form></div>

  <div v-if="milestoneTarget" class="modal-backdrop" @click.self="milestoneTarget = null"><form class="user-modal finance-modal" @submit.prevent="saveMilestones">
    <h2>Milestones for {{ milestoneTarget.title }}</h2>
    <div v-for="(row, index) in milestoneRows" :key="index" class="form-grid" style="border-bottom:1px solid var(--border-color, #e5e5e5);padding-bottom:8px;margin-bottom:8px">
      <label>Title<input v-model="row.title" required /></label>
      <label>Due date<input v-model="row.due_date" type="date" /></label>
      <label>Amount<input v-model.number="row.amount" type="number" min="0" step="0.01" /></label>
      <button type="button" class="secondary-action compact-action" @click="removeMilestoneRow(index)"><Trash2 :size="14" /> Remove</button>
    </div>
    <button type="button" class="secondary-action compact-action" @click="addMilestoneRow"><Plus :size="14" /> Add milestone</button>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="milestoneTarget = null">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save milestones" }}</button></footer>
  </form></div>
</template>
