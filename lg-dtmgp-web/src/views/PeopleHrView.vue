<script setup lang="ts">
import { BadgeCheck, CalendarDays, ChevronLeft, ChevronRight, CircleAlert, Pencil, Search, UserPlus, UsersRound } from "@lucide/vue";
import { ref, watch } from "vue";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Dashboard { total: number; active: number; verified: number; on_leave: number; needs_attention: number; can_manage: boolean }
interface Employee { name: string; employee_name: string; first_name: string; last_name: string; company: string; department: string | null; designation: string | null; status: string; date_of_joining: string; date_of_birth: string; gender: string; dtmgp_grade_level: string; dtmgp_verification_status: string }
interface Options { departments: string[]; designations: string[]; genders: string[]; statuses: string[]; verification_statuses: string[] }
interface Leave { name: string; employee_name: string; leave_type: string; from_date: string; to_date: string; total_leave_days: number; status: string }
interface Department { name: string; department_name: string; company: string; employee_count: number }

const session = useSessionStore();
const tabs = ["Staff directory", "Verification", "Leave & attendance", "Establishment"];
const activeTab = ref(tabs[0]);
const dashboard = ref<Dashboard | null>(null);
const employees = ref<Employee[]>([]);
const options = ref<Options>({ departments: [], designations: [], genders: [], statuses: [], verification_statuses: [] });
const leave = ref<Leave[]>([]);
const departments = ref<Department[]>([]);
const search = ref("");
const department = ref("");
const page = ref(1);
const total = ref(0);
const pageSize = 25;
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const editing = ref<string | null>(null);
const saving = ref(false);
const form = ref(emptyForm());

function emptyForm() {
  return { first_name: "", last_name: "", company: session.activeLga, gender: "", date_of_birth: "", date_of_joining: "", department: "", designation: "", grade_level: "", status: "Active", verification_status: "Pending" };
}
function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }
function initials(name: string) { return name.split(" ").filter(Boolean).map(part => part[0]).slice(0, 2).join(""); }
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }

async function loadModule() {
  loading.value = true;
  error.value = "";
  page.value = 1;
  try {
    const [summary, formOptions] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.people.get_dashboard?${scopeQuery()}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.people.get_form_options?${scopeQuery()}`),
    ]);
    dashboard.value = summary;
    options.value = formOptions;
    await loadEmployees();
    if (activeTab.value === "Leave & attendance") await loadLeave();
    if (activeTab.value === "Establishment") await loadEstablishment();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load People and HR";
  } finally {
    loading.value = false;
  }
}

async function loadEmployees() {
  const params = new URLSearchParams({ company: session.activeLga, page: String(page.value), page_size: String(pageSize) });
  if (search.value.trim()) params.set("search", search.value.trim());
  if (department.value) params.set("department", department.value);
  const result = await apiRequest<{ items: Employee[]; total: number }>(`/api/method/dtmgp.api.v1.people.list_employees?${params}`);
  employees.value = result.items;
  total.value = result.total;
}

async function selectTab(tab: string) {
  activeTab.value = tab;
  if (tab === "Leave & attendance") await loadLeave();
  if (tab === "Establishment") await loadEstablishment();
}
async function loadLeave() { leave.value = await apiRequest<Leave[]>(`/api/method/dtmgp.api.v1.people.list_leave?${scopeQuery()}`); }
async function loadEstablishment() { departments.value = await apiRequest<Department[]>(`/api/method/dtmgp.api.v1.people.get_establishment?${scopeQuery()}`); }
async function applyFilters() { page.value = 1; await loadEmployees(); }
async function changePage(change: number) { page.value += change; await loadEmployees(); }

function openCreate() { editing.value = null; form.value = emptyForm(); showForm.value = true; }
function openEdit(employee: Employee) {
  editing.value = employee.name;
  form.value = { first_name: employee.first_name, last_name: employee.last_name || "", company: employee.company, gender: employee.gender, date_of_birth: employee.date_of_birth, date_of_joining: employee.date_of_joining, department: employee.department || "", designation: employee.designation || "", grade_level: employee.dtmgp_grade_level || "", status: employee.status, verification_status: employee.dtmgp_verification_status || "Pending" };
  showForm.value = true;
}
async function saveEmployee() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.people.save_employee", { method: "POST", body: JSON.stringify({ ...form.value, employee: editing.value }) });
    showForm.value = false;
    await loadModule();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to save employee";
  } finally { saving.value = false; }
}
async function verify(employee: Employee) {
  await apiRequest("/api/method/dtmgp.api.v1.people.set_verification", { method: "POST", body: JSON.stringify({ employee: employee.name, verification_status: "Verified" }) });
  await loadModule();
}

watch(() => session.activeLga, loadModule, { immediate: true });
</script>

<template>
  <section class="hr-heading">
    <div><p class="eyebrow">{{ shortLga() }}</p><h1>People & HR</h1><p>Workforce records, verification, leave and establishment</p></div>
    <button v-if="dashboard?.can_manage" class="primary-action" @click="openCreate"><UserPlus :size="17" /> Add employee</button>
  </section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading workforce records...</section>
  <template v-else-if="dashboard">
    <section class="hr-metrics" aria-label="Workforce summary">
      <article><span class="hr-metric-icon green"><UsersRound :size="19" /></span><div><small>Total staff</small><strong>{{ dashboard.total }}</strong><p>{{ dashboard.active }} active</p></div></article>
      <article><span class="hr-metric-icon blue"><BadgeCheck :size="19" /></span><div><small>Verified records</small><strong>{{ dashboard.verified }}</strong><p>{{ dashboard.total ? Math.round(dashboard.verified / dashboard.total * 100) : 0 }}% complete</p></div></article>
      <article><span class="hr-metric-icon gold"><CalendarDays :size="19" /></span><div><small>On leave</small><strong>{{ dashboard.on_leave }}</strong><p>Approved leave today</p></div></article>
      <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Needs attention</small><strong>{{ dashboard.needs_attention }}</strong><p>Records to verify</p></div></article>
    </section>

    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="People and HR views"><button v-for="tab in tabs" :key="tab" :class="{ active: activeTab === tab }" @click="selectTab(tab)">{{ tab }}</button></nav>
      <template v-if="activeTab === 'Staff directory' || activeTab === 'Verification'">
        <form class="directory-toolbar" @submit.prevent="applyFilters"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search name, ID or designation" /></label><select v-model="department" class="toolbar-select"><option value="">All departments</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select><button class="secondary-action">Apply</button></form>
        <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Grade</th><th>Employment</th><th>Verification</th><th></th></tr></thead><tbody>
          <tr v-for="person in employees" :key="person.name"><td><div class="staff-person"><span>{{ initials(person.employee_name) }}</span><div><strong>{{ person.employee_name }}</strong><small>{{ person.name }} · {{ person.designation || "No designation" }}</small></div></div></td><td>{{ person.department || "Unassigned" }}</td><td>{{ person.dtmgp_grade_level || "-" }}</td><td><span class="table-status" :class="person.status === 'Active' ? 'success' : 'neutral'">{{ person.status }}</span></td><td><span class="verification-status" :class="person.dtmgp_verification_status === 'Verified' ? 'verified' : 'pending'">{{ person.dtmgp_verification_status || "Pending" }}</span></td><td><button v-if="dashboard.can_manage && activeTab === 'Staff directory'" class="icon-button" title="Edit employee" @click="openEdit(person)"><Pencil :size="17" /></button><button v-else-if="dashboard.can_manage && person.dtmgp_verification_status !== 'Verified'" class="secondary-action compact-action" @click="verify(person)"><BadgeCheck :size="15" /> Verify</button></td></tr>
        </tbody></table><footer class="table-footer"><span>Showing {{ employees.length }} of {{ total }} staff</span><div><button :disabled="page === 1" @click="changePage(-1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * pageSize >= total" @click="changePage(1)">Next <ChevronRight :size="14" /></button></div></footer></div>
      </template>
      <div v-else-if="activeTab === 'Leave & attendance'" class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>From</th><th>To</th><th>Days</th><th>Status</th></tr></thead><tbody><tr v-for="item in leave" :key="item.name"><td>{{ item.employee_name }}</td><td>{{ item.leave_type }}</td><td>{{ item.from_date }}</td><td>{{ item.to_date }}</td><td>{{ item.total_leave_days }}</td><td><span class="table-status" :class="item.status === 'Approved' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="!leave.length" class="users-empty">No leave applications in this LGA.</p></div>
      <div v-else class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>LGA</th><th>Active employees</th></tr></thead><tbody><tr v-for="item in departments" :key="item.name"><td>{{ item.department_name }}</td><td>{{ item.company.replace(' Local Government Area', ' LGA') }}</td><td>{{ item.employee_count }}</td></tr></tbody></table><p v-if="!departments.length" class="users-empty">No departments configured for this LGA.</p></div>
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal employee-modal" @submit.prevent="saveEmployee"><h2>{{ editing ? "Edit employee" : "Add employee" }}</h2><div class="form-grid"><label>First name<input v-model="form.first_name" required /></label><label>Last name<input v-model="form.last_name" /></label><label>Gender<select v-model="form.gender" required><option value="" disabled>Select gender</option><option v-for="item in options.genders" :key="item">{{ item }}</option></select></label><label>Date of birth<input v-model="form.date_of_birth" type="date" required /></label><label>Date joined<input v-model="form.date_of_joining" type="date" required /></label><label>Department<select v-model="form.department"><option value="">Unassigned</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Designation<select v-model="form.designation"><option value="">Unassigned</option><option v-for="item in options.designations" :key="item">{{ item }}</option></select></label><label>Grade level<input v-model="form.grade_level" placeholder="GL 08" /></label><label>Employment status<select v-model="form.status"><option v-for="item in options.statuses" :key="item">{{ item }}</option></select></label><label>Verification<select v-model="form.verification_status"><option v-for="item in options.verification_statuses" :key="item">{{ item }}</option></select></label></div><p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save employee" }}</button></footer></form></div>
</template>
