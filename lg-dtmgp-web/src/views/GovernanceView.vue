<script setup lang="ts">
import { Building2, ClipboardCheck, FilePlus2, Inbox, Mail, Search, Send } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Dashboard {
  scope: string;
  can_manage: boolean;
  correspondence: { draft: number; registered: number; dispatched: number; overdue_assigned: number };
  departments: number;
}
interface CorrespondenceItem { name: string; correspondence_type: string; subject: string; correspondent: string; department: string | null; correspondence_date: string; priority: string; status: string; assigned_to: string | null; due_date: string | null }
interface DepartmentItem { name: string; department_name: string; company: string; disabled: number; is_group: number; parent_department: string | null }
interface Options { departments: string[]; users: { name: string; full_name: string }[] }

const NEXT_STATUS: Record<string, string[]> = { Draft: ["Registered"], Registered: ["Dispatched", "Closed"], Dispatched: ["Closed"], Closed: [] };

const session = useSessionStore();
const tabs = [
  { key: "correspondence", label: "Correspondence" },
  { key: "departments", label: "Departments & Units" },
];
const active = ref(tabs[0]);
const dashboard = ref<Dashboard | null>(null);
const options = ref<Options>({ departments: [], users: [] });
const correspondence = ref<CorrespondenceItem[]>([]);
const departments = ref<DepartmentItem[]>([]);
const total = ref(0);
const search = ref("");
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const saving = ref(false);
const today = () => new Date().toISOString().slice(0, 10);
const correspondenceForm = ref(emptyCorrespondenceForm());
const departmentForm = ref(emptyDepartmentForm());

function emptyCorrespondenceForm() {
  return { company: session.activeLga, correspondence_type: "Incoming", subject: "", correspondent: "", department: "", correspondence_date: today(), priority: "Routine", assigned_to: "", due_date: "", summary: "" };
}
function emptyDepartmentForm() {
  return { company: session.activeLga, department_name: "", parent_department: "" };
}

async function loadModule() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [dashboard.value, options.value] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.governance.get_dashboard?company=${company}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.governance.get_form_options?company=${company}`),
    ]);
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load governance workspace"; }
  finally { loading.value = false; }
}
async function loadRecords() {
  if (active.value.key === "departments") {
    departments.value = await apiRequest<DepartmentItem[]>(`/api/method/dtmgp.api.v1.governance.list_departments?company=${encodeURIComponent(session.activeLga)}`);
    total.value = departments.value.length;
    return;
  }
  const params = new URLSearchParams({ doctype: "DTMGP Correspondence", company: session.activeLga });
  if (search.value.trim()) params.set("search", search.value.trim());
  const result = await apiRequest<{ items: CorrespondenceItem[]; total: number }>(`/api/method/dtmgp.api.v1.governance.list_records?${params}`);
  correspondence.value = result.items; total.value = result.total;
}
async function chooseTab(tab: typeof tabs[number]) { active.value = tab; search.value = ""; await loadRecords(); }
function openCreate() {
  correspondenceForm.value = emptyCorrespondenceForm();
  departmentForm.value = emptyDepartmentForm();
  showForm.value = true;
}
async function saveCorrespondence() {
  saving.value = true; error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Correspondence", values: correspondenceForm.value }) });
    showForm.value = false; await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save correspondence"; }
  finally { saving.value = false; }
}
async function saveDepartment() {
  saving.value = true; error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.save_department", { method: "POST", body: JSON.stringify({ values: departmentForm.value }) });
    showForm.value = false; await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save department"; }
  finally { saving.value = false; }
}
async function transition(item: CorrespondenceItem, targetStatus: string) {
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Correspondence", name: item.name, target_status: targetStatus }) });
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update status"; }
}

watch(() => session.activeLga, loadModule, { immediate: true });
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ dashboard?.scope || session.activeLga }}</p><h1>Administration & Governance</h1><p>Correspondence, departments and units for the LGA secretariat</p></div><button v-if="dashboard?.can_manage" class="primary-action" @click="openCreate"><FilePlus2 :size="17" /> New {{ active.label === 'Correspondence' ? 'correspondence' : 'department' }}</button></section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading governance records...</section>
  <template v-else-if="dashboard">
    <section class="finance-metrics" aria-label="Governance summary">
      <article><span class="hr-metric-icon blue"><Inbox :size="19" /></span><div><small>Draft correspondence</small><strong>{{ dashboard.correspondence.draft }}</strong><p>{{ dashboard.correspondence.registered }} registered</p></div></article>
      <article><span class="hr-metric-icon green"><Send :size="19" /></span><div><small>Dispatched</small><strong>{{ dashboard.correspondence.dispatched }}</strong><p>{{ dashboard.correspondence.overdue_assigned }} overdue</p></div></article>
      <article><span class="hr-metric-icon gold"><Building2 :size="19" /></span><div><small>Departments &amp; units</small><strong>{{ dashboard.departments }}</strong><p>Active in {{ session.activeLga }}</p></div></article>
      <article><span class="hr-metric-icon red"><ClipboardCheck :size="19" /></span><div><small>Assigned to me</small><strong>{{ correspondence.filter(item => item.assigned_to === session.user.email).length }}</strong><p>Awaiting action</p></div></article>
    </section>
    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="Governance views"><button v-for="tab in tabs" :key="tab.key" :class="{ active: active.key === tab.key }" @click="chooseTab(tab)">{{ tab.label }}</button></nav>
      <form v-if="active.key === 'correspondence'" class="directory-toolbar" @submit.prevent="loadRecords"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search correspondence" /></label><button class="secondary-action">Search</button></form>

      <div v-if="active.key === 'correspondence'" class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Reference</th><th>Type</th><th>Subject</th><th>From / To</th><th>Date</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            <tr v-for="item in correspondence" :key="item.name">
              <td><strong>{{ item.name }}</strong></td>
              <td><Mail :size="14" /> {{ item.correspondence_type }}</td>
              <td>{{ item.subject }}</td>
              <td>{{ item.correspondent || '-' }}</td>
              <td>{{ item.correspondence_date }}</td>
              <td><span class="table-status" :class="item.status === 'Closed' ? 'success' : 'neutral'">{{ item.status }}</span></td>
              <td><button v-for="next in NEXT_STATUS[item.status]" :key="next" class="secondary-action" type="button" @click="transition(item, next)">{{ next }}</button></td>
            </tr>
          </tbody>
        </table>
        <p v-if="!correspondence.length" class="users-empty">No correspondence records in this LGA.</p>
        <footer class="table-footer"><span>{{ total }} records</span><span>Scoped to {{ session.activeLga }}</span></footer>
      </div>

      <div v-else class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Department</th><th>Parent</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="item in departments" :key="item.name">
              <td><strong>{{ item.department_name }}</strong></td>
              <td>{{ item.parent_department || '-' }}</td>
              <td><span class="table-status" :class="item.disabled ? 'neutral' : 'success'">{{ item.disabled ? 'Disabled' : 'Active' }}</span></td>
            </tr>
          </tbody>
        </table>
        <p v-if="!departments.length" class="users-empty">No departments or units registered in this LGA.</p>
        <footer class="table-footer"><span>{{ total }} departments</span><span>Scoped to {{ session.activeLga }}</span></footer>
      </div>
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
    <form v-if="active.key === 'correspondence'" class="user-modal finance-modal" @submit.prevent="saveCorrespondence">
      <h2>New correspondence</h2>
      <div class="form-grid">
        <label>Type<select v-model="correspondenceForm.correspondence_type"><option>Incoming</option><option>Outgoing</option><option>Internal Memo</option></select></label>
        <label>Priority<select v-model="correspondenceForm.priority"><option>Routine</option><option>Urgent</option><option>Confidential</option></select></label>
        <label class="full-field">Subject<input v-model="correspondenceForm.subject" required /></label>
        <label>Sender / recipient<input v-model="correspondenceForm.correspondent" /></label>
        <label>Department<select v-model="correspondenceForm.department"><option value="">Unassigned</option><option v-for="item in options.departments" :key="item" :value="item">{{ item }}</option></select></label>
        <label>Date<input v-model="correspondenceForm.correspondence_date" type="date" required /></label>
        <label>Due date<input v-model="correspondenceForm.due_date" type="date" /></label>
        <label>Assigned to<select v-model="correspondenceForm.assigned_to"><option value="">Unassigned</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label class="full-field">Summary<textarea v-model="correspondenceForm.summary"></textarea></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save correspondence' }}</button></footer>
    </form>
    <form v-else class="user-modal finance-modal" @submit.prevent="saveDepartment">
      <h2>New department / unit</h2>
      <div class="form-grid">
        <label class="full-field">Name<input v-model="departmentForm.department_name" required /></label>
        <label>Parent department<select v-model="departmentForm.parent_department"><option value="">None</option><option v-for="item in options.departments" :key="item" :value="item">{{ item }}</option></select></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save department' }}</button></footer>
    </form>
  </div>
</template>
