<script setup lang="ts">
import { ClipboardList, Plus } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { today } from "@/views/finance/types";
import type { ApprovalLimit } from "@/views/finance/types";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { ApprovalDelegation } from "./types";

const ITEM_LABELS: Record<string, string> = { "approval-limits": "Approval Limits", "approval-delegation": "Approval Delegation", workflows: "Workflows", "workflow-states": "Workflow States", "escalation-rules": "Escalation Rules" };
const DEFAULT_ITEM = "approval-limits";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const TRANSACTION_TYPES = ["Payment Request", "Procurement Plan", "Procurement Award", "Contract Variation", "Revenue Adjustment"];

const session = useSessionStore();
const limits = ref<ApprovalLimit[]>([]);
const delegations = ref<ApprovalDelegation[]>([]);
const roles = ref<string[]>([]);
const users = ref<{ name: string; full_name: string }[]>([]);
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const formKind = ref<"limit" | "delegation">("limit");
const form = ref<Record<string, string | number>>({});
const saving = ref(false);

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }

async function load() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    const [limitResult, delegationResult, options] = await Promise.all([
      apiRequest<{ items: ApprovalLimit[] }>(`/api/method/dtmgp.api.v1.finance.list_records?doctype=${encodeURIComponent("DTMGP Approval Limit")}&${scopeQuery()}&page_size=100`),
      apiRequest<{ items: ApprovalDelegation[] }>(`/api/method/dtmgp.api.v1.governance.list_records?doctype=${encodeURIComponent("DTMGP Approval Delegation")}&${scopeQuery()}&page_size=100`),
      apiRequest<{ roles: string[]; users: { name: string; full_name: string }[] }>(`/api/method/dtmgp.api.v1.governance.get_form_options?${scopeQuery()}`),
    ]);
    limits.value = limitResult.items;
    delegations.value = delegationResult.items;
    roles.value = options.roles;
    users.value = options.users;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load Workflow Setup"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, load, { immediate: true });

function openForm(kind: typeof formKind.value) {
  formKind.value = kind;
  form.value = kind === "limit"
    ? { company: session.activeLga, transaction_type: TRANSACTION_TYPES[0], approving_role: roles.value[0] || "", minimum_amount: 0, maximum_amount: 0, active: 1 }
    : { company: session.activeLga, delegator: "", delegate: "", role: roles.value[0] || "", start_date: today(), end_date: today(), active: 1 };
  showForm.value = true;
}

async function saveForm() {
  saving.value = true;
  error.value = "";
  try {
    const doctype = formKind.value === "limit" ? "DTMGP Approval Limit" : "DTMGP Approval Delegation";
    const api = formKind.value === "limit" ? "dtmgp.api.v1.finance.save_record" : "dtmgp.api.v1.governance.save_record";
    await apiRequest(`/api/method/${api}`, { method: "POST", body: JSON.stringify({ doctype, values: form.value }) });
    showForm.value = false;
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the record"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>
  <template v-else>
    <template v-if="activeItem === 'approval-limits'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Approval limits</h3><button class="secondary-action" @click="openForm('limit')"><Plus :size="15" /> New approval limit</button></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Transaction type</th><th>Approving role</th><th>Minimum</th><th>Maximum</th><th>Active</th></tr></thead><tbody><tr v-for="item in limits" :key="item.name" v-record="{ doctype: 'DTMGP Approval Limit', name: item.name }"><td>{{ item.transaction_type }}</td><td><strong>{{ item.approving_role }}</strong></td><td>{{ item.minimum_amount }}</td><td>{{ item.maximum_amount }}</td><td><span class="table-status" :class="item.active ? 'success' : 'neutral'">{{ item.active ? "Active" : "Inactive" }}</span></td></tr></tbody></table><p v-if="!limits.length" class="users-empty">No approval limits configured for this LGA — amount-gated transitions will be denied until one exists.</p></div>
    </template>

    <template v-else-if="activeItem === 'approval-delegation'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Approval delegations</h3><button class="secondary-action" @click="openForm('delegation')"><Plus :size="15" /> New delegation</button></div>
      <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Delegator</th><th>Delegate</th><th>Role</th><th>Until</th><th>Active</th></tr></thead><tbody><tr v-for="item in delegations" :key="item.name" v-record="{ doctype: 'DTMGP Approval Delegation', name: item.name }"><td>{{ item.delegator }}</td><td>{{ item.delegate }}</td><td><strong>{{ item.role }}</strong></td><td>{{ item.end_date }}</td><td><span class="table-status" :class="item.active ? 'success' : 'neutral'">{{ item.active ? "Active" : "Inactive" }}</span></td></tr></tbody></table><p v-if="!delegations.length" class="users-empty">No approval delegations recorded for this LGA.</p></div>
    </template>

    <template v-else-if="activeItem === 'workflows' || activeItem === 'workflow-states'">
      <PreviewCard :icon="ClipboardList" title="Not applicable to this platform" body="DTMGP doesn't use Frappe's generic Workflow engine — each domain (Finance, Governance, Traditional Affairs, Projects) enforces its own explicit status transitions in code, reviewed and tested per domain. There is no generic workflow/workflow-state configuration to expose here." />
    </template>

    <template v-else-if="activeItem === 'escalation-rules'">
      <PreviewCard :icon="ClipboardList" title="Escalation rules" body="Deduplicated reminders and escalations for overdue returns, actions and inspections are listed as pending platform work (see docs/implementation-status.md's Notifications backlog item), not yet built." />
    </template>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal finance-modal" @submit.prevent="saveForm">
    <template v-if="formKind === 'limit'">
      <h2>New approval limit</h2>
      <div class="form-grid">
        <label>Transaction type<select v-model="form.transaction_type"><option v-for="type in TRANSACTION_TYPES" :key="type">{{ type }}</option></select></label>
        <label>Approving role<select v-model="form.approving_role" required><option value="" disabled>Select role</option><option v-for="role in roles" :key="role" :value="role">{{ role }}</option></select></label>
        <label>Minimum amount<input v-model.number="form.minimum_amount" type="number" min="0" step="0.01" required /></label>
        <label>Maximum amount<input v-model.number="form.maximum_amount" type="number" min="0.01" step="0.01" required /></label>
      </div>
    </template>
    <template v-else>
      <h2>New approval delegation</h2>
      <div class="form-grid">
        <label>Delegator<select v-model="form.delegator" required><option value="" disabled>Select delegator</option><option v-for="user in users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label>Delegate<select v-model="form.delegate" required><option value="" disabled>Select delegate</option><option v-for="user in users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label>Delegated role<select v-model="form.role" required><option value="" disabled>Select role</option><option v-for="role in roles" :key="role" :value="role">{{ role }}</option></select></label>
        <label>Until<input v-model="form.end_date" type="date" required /></label>
      </div>
    </template>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save" }}</button></footer>
  </form></div>
</template>
