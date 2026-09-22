<script setup lang="ts">
import { ChevronLeft, ChevronRight, Pencil, Search } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Employee } from "./types";
import { initials } from "./types";

interface EmergencyContact { person_to_be_contacted: string | null; relation: string | null; emergency_phone_number: string | null }
interface WorkHistoryRow { department: string | null; designation: string | null; branch: string | null; from_date: string | null; to_date: string | null }
interface ExternalHistoryRow { company_name: string | null; designation: string | null; contact: string | null; total_experience: number | null }
interface EmployeeProfile { name: string; employee_name: string; company: string; department: string | null; designation: string | null; status: string; gender: string; date_of_birth: string; date_of_joining: string; grade_level: string | null; verification_status: string | null; cell_number: string | null; personal_email: string | null; emergency_contact: EmergencyContact; internal_work_history: WorkHistoryRow[]; external_work_history: ExternalHistoryRow[] }
interface DocumentRow { name: string; file_name: string; file_url: string; is_private: number; creation: string }

const PROFILE_ITEMS = new Set(["staff-profiles", "digital-personnel-files", "employment-history", "next-of-kin", "staff-documents"]);

defineProps<{ employees: Employee[]; total: number; page: number; pageSize: number; departmentOptions: string[]; canManage: boolean }>();
const search = defineModel<string>("search", { required: true });
const department = defineModel<string>("department", { required: true });
defineEmits<{ "apply-filters": []; "change-page": [change: number]; "edit-employee": [employee: Employee] }>();

const ITEM_LABELS: Record<string, string> = { "staff-directory": "Staff Directory", "staff-profiles": "Staff Profiles", "digital-personnel-files": "Digital Personnel Files", "employment-history": "Employment History", "next-of-kin": "Next of Kin", "staff-documents": "Staff Documents" };
const DEFAULT_ITEM = "staff-directory";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const selectedEmployee = ref("");
const profile = ref<EmployeeProfile | null>(null);
const profileLoading = ref(false);
const profileError = ref("");
const documents = ref<DocumentRow[]>([]);
const documentsLoading = ref(false);
const documentsFor = ref("");
const DOCUMENT_ITEMS = new Set(["digital-personnel-files", "staff-documents"]);

async function loadProfile(employee: string) {
  if (!employee) { profile.value = null; return; }
  profileLoading.value = true;
  profileError.value = "";
  try { profile.value = await apiRequest<EmployeeProfile>(`/api/method/dtmgp.api.v1.people.get_employee_profile?employee=${encodeURIComponent(employee)}`); }
  catch (reason) { profileError.value = reason instanceof Error ? reason.message : "Unable to load the employee profile"; }
  finally { profileLoading.value = false; }
}
async function ensureDocuments(employee: string) {
  if (!employee || documentsFor.value === employee) return;
  documentsLoading.value = true;
  try { documents.value = await apiRequest<DocumentRow[]>(`/api/method/dtmgp.api.v1.people.list_employee_documents?employee=${encodeURIComponent(employee)}`); documentsFor.value = employee; }
  finally { documentsLoading.value = false; }
}
watch(selectedEmployee, (employee) => { loadProfile(employee); if (employee && DOCUMENT_ITEMS.has(activeItem.value)) ensureDocuments(employee); });
watch(activeItem, (item) => { if (selectedEmployee.value && DOCUMENT_ITEMS.has(item)) ensureDocuments(selectedEmployee.value); });

const showPicker = computed(() => PROFILE_ITEMS.has(activeItem.value));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'staff-directory'">
    <form class="directory-toolbar" @submit.prevent="$emit('apply-filters')"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search name, ID or designation" /></label><select v-model="department" class="toolbar-select"><option value="">All departments</option><option v-for="item in departmentOptions" :key="item">{{ item }}</option></select><button class="secondary-action">Apply</button></form>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Grade</th><th>Employment</th><th>Verification</th><th></th></tr></thead><tbody>
      <tr v-for="person in employees" :key="person.name"><td><div class="staff-person"><span>{{ initials(person.employee_name) }}</span><div><strong>{{ person.employee_name }}</strong><small>{{ person.name }} · {{ person.designation || "No designation" }}</small></div></div></td><td>{{ person.department || "Unassigned" }}</td><td>{{ person.dtmgp_grade_level || "-" }}</td><td><span class="table-status" :class="person.status === 'Active' ? 'success' : 'neutral'">{{ person.status }}</span></td><td><span class="verification-status" :class="person.dtmgp_verification_status === 'Verified' ? 'verified' : 'pending'">{{ person.dtmgp_verification_status || "Pending" }}</span></td><td><button v-if="canManage" class="icon-button" title="Edit employee" @click="$emit('edit-employee', person)"><Pencil :size="17" /></button></td></tr>
    </tbody></table><footer class="table-footer"><span>Showing {{ employees.length }} of {{ total }} staff</span><div><button :disabled="page === 1" @click="$emit('change-page', -1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * pageSize >= total" @click="$emit('change-page', 1)">Next <ChevronRight :size="14" /></button></div></footer></div>
  </template>

  <template v-else-if="showPicker">
    <div class="directory-toolbar"><label style="flex:1;max-width:360px">Staff member<select v-model="selectedEmployee"><option value="">Select a staff member</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }} — {{ item.name }}</option></select></label></div>
    <p v-if="!selectedEmployee" class="users-empty">Select a staff member above to view their record.</p>
    <p v-else-if="profileLoading" class="users-empty">Loading record...</p>
    <p v-else-if="profileError" class="login-error" role="alert">{{ profileError }}</p>

    <template v-else-if="profile && activeItem === 'staff-profiles'">
      <div class="staff-table-wrap"><table class="staff-table"><tbody>
        <tr><td>Name</td><td>{{ profile.employee_name }}</td></tr>
        <tr><td>Department</td><td>{{ profile.department || '-' }}</td></tr>
        <tr><td>Designation</td><td>{{ profile.designation || '-' }}</td></tr>
        <tr><td>Grade level</td><td>{{ profile.grade_level || '-' }}</td></tr>
        <tr><td>Status</td><td>{{ profile.status }}</td></tr>
        <tr><td>Gender</td><td>{{ profile.gender }}</td></tr>
        <tr><td>Date of birth</td><td>{{ profile.date_of_birth }}</td></tr>
        <tr><td>Date joined</td><td>{{ profile.date_of_joining }}</td></tr>
        <tr><td>Cell number</td><td>{{ profile.cell_number || '-' }}</td></tr>
        <tr><td>Personal email</td><td>{{ profile.personal_email || '-' }}</td></tr>
        <tr><td>Verification status</td><td>{{ profile.verification_status || 'Pending' }}</td></tr>
      </tbody></table></div>
    </template>

    <template v-else-if="profile && activeItem === 'digital-personnel-files'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Record summary</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><tbody>
        <tr><td>Name</td><td>{{ profile.employee_name }}</td></tr>
        <tr><td>Department / designation</td><td>{{ profile.department || '-' }} / {{ profile.designation || '-' }}</td></tr>
        <tr><td>Grade level</td><td>{{ profile.grade_level || '-' }}</td></tr>
      </tbody></table></div>
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Documents on file</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Document</th><th>Visibility</th><th>Uploaded</th></tr></thead><tbody><tr v-for="row in documents" :key="row.name"><td><a :href="row.file_url" target="_blank" rel="noopener">{{ row.file_name }}</a></td><td>{{ row.is_private ? "Private" : "Public" }}</td><td>{{ row.creation }}</td></tr></tbody></table><p v-if="documentsLoading" class="users-empty">Loading documents...</p><p v-else-if="!documents.length" class="users-empty">No documents on file for this staff member.</p></div>
    </template>

    <template v-else-if="profile && activeItem === 'employment-history'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Internal postings</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>Designation</th><th>Branch</th><th>From</th><th>To</th></tr></thead><tbody><tr v-for="(row, index) in profile.internal_work_history" :key="index"><td>{{ row.department || '-' }}</td><td>{{ row.designation || '-' }}</td><td>{{ row.branch || '-' }}</td><td>{{ row.from_date || '-' }}</td><td>{{ row.to_date || '-' }}</td></tr></tbody></table><p v-if="!profile.internal_work_history.length" class="users-empty">No internal posting history recorded.</p></div>
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">External experience</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Organisation</th><th>Designation</th><th>Contact</th><th>Experience (years)</th></tr></thead><tbody><tr v-for="(row, index) in profile.external_work_history" :key="index"><td>{{ row.company_name || '-' }}</td><td>{{ row.designation || '-' }}</td><td>{{ row.contact || '-' }}</td><td>{{ row.total_experience ?? '-' }}</td></tr></tbody></table><p v-if="!profile.external_work_history.length" class="users-empty">No external experience recorded.</p></div>
    </template>

    <template v-else-if="profile && activeItem === 'next-of-kin'">
      <p class="users-empty" style="text-align:left;padding:12px 20px 0">Only a single emergency contact per staff member is currently recorded on the Employee record; a dedicated multi-entry next-of-kin list isn't modeled yet.</p>
      <div class="staff-table-wrap"><table class="staff-table"><tbody>
        <tr><td>Contact person</td><td>{{ profile.emergency_contact.person_to_be_contacted || '-' }}</td></tr>
        <tr><td>Relationship</td><td>{{ profile.emergency_contact.relation || '-' }}</td></tr>
        <tr><td>Phone</td><td>{{ profile.emergency_contact.emergency_phone_number || '-' }}</td></tr>
      </tbody></table></div>
    </template>

    <template v-else-if="activeItem === 'staff-documents'">
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Document</th><th>Visibility</th><th>Uploaded</th></tr></thead><tbody><tr v-for="row in documents" :key="row.name"><td><a :href="row.file_url" target="_blank" rel="noopener">{{ row.file_name }}</a></td><td>{{ row.is_private ? "Private" : "Public" }}</td><td>{{ row.creation }}</td></tr></tbody></table><p v-if="documentsLoading" class="users-empty">Loading documents...</p><p v-else-if="!documents.length" class="users-empty">No documents on file for this staff member.</p></div>
    </template>
  </template>
</template>
