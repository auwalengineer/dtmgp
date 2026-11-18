<script setup lang="ts">
import { Camera, ChevronLeft, ChevronRight, FilePlus2, Pencil, Plus, Search, Trash2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest, uploadFile } from "@/services/api";

import ItemTabs from "../shared/ItemTabs.vue";
import EmployeeAvatar from "./EmployeeAvatar.vue";
import EmployeeEditModal from "./EmployeeEditModal.vue";
import type { Employee, Options } from "./types";

interface EmergencyContact { person_to_be_contacted: string | null; relation: string | null; emergency_phone_number: string | null }
interface WorkHistoryRow { department: string | null; designation: string | null; branch: string | null; from_date: string | null; to_date: string | null }
interface ExternalHistoryRow { company_name: string | null; designation: string | null; contact: string | null; total_experience: number | null }
interface EmployeeProfile { name: string; employee_name: string; image: string | null; company: string; department: string | null; designation: string | null; status: string; gender: string; date_of_birth: string; date_of_joining: string; grade_level: string | null; verification_status: string | null; cell_number: string | null; personal_email: string | null; emergency_contact: EmergencyContact; internal_work_history: WorkHistoryRow[]; external_work_history: ExternalHistoryRow[] }
interface DocumentRow { name: string; file_name: string; file_url: string; is_private: number; creation: string }
interface PersonnelFile { name: string; file_status: string; classification: string; retention_category: string; retention_review_date?: string; physical_file_reference?: string }
interface NextOfKin { name: string; full_name: string; relationship: string; phone: string; alternate_phone?: string; email?: string; address?: string; is_primary: number; verified_on?: string }
interface StaffDocument { name: string; document_type: string; document_date?: string; expiry_date?: string; reference_number?: string; file: string; classification: string; retention_category: string; retention_review_date?: string; verification_status: string }

const PROFILE_ITEMS = new Set(["staff-profiles", "digital-personnel-files", "employment-history", "next-of-kin", "staff-documents"]);

defineProps<{ employees: Employee[]; total: number; page: number; pageSize: number; departmentOptions: string[]; canManage: boolean; formOptions: Options }>();
const search = defineModel<string>("search", { required: true });
const department = defineModel<string>("department", { required: true });
const emit = defineEmits<{ "apply-filters": []; "change-page": [change: number]; "employee-saved": []; "photo-changed": [] }>();

const ITEM_LABELS: Record<string, string> = { "staff-directory": "Staff Directory", "staff-profiles": "Staff Profiles", "digital-personnel-files": "Digital Personnel Files", "employment-history": "Employment History", "next-of-kin": "Next of Kin", "staff-documents": "Staff Documents" };
const DEFAULT_ITEM = "staff-directory";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const selectedEmployee = ref("");
const editingEmployee = ref<string | null>(null);
const savedNotice = ref("");
const profile = ref<EmployeeProfile | null>(null);
const profileLoading = ref(false);
const profileError = ref("");
const documents = ref<DocumentRow[]>([]);
const documentsLoading = ref(false);
const documentsFor = ref("");
const personnelFiles = ref<PersonnelFile[]>([]);
const nextOfKin = ref<NextOfKin[]>([]);
const staffDocuments = ref<StaffDocument[]>([]);
const recordLoading = ref(false);
const recordError = ref("");
const showRecordForm = ref(false);
const recordKind = ref<"personnel_file" | "next_of_kin" | "staff_document">("personnel_file");
const recordForm = ref<Record<string, string | number>>({});
const pendingDocument = ref<File | null>(null);
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
async function loadRestrictedRecords(employee: string) {
  if (!employee) return;
  recordLoading.value = true;
  recordError.value = "";
  try {
    const endpoint = "/api/method/dtmgp.api.v1.hr.list_restricted_hr_records";
    const query = (type: string) => `${endpoint}?record_type=${type}&employee=${encodeURIComponent(employee)}`;
    [personnelFiles.value, nextOfKin.value, staffDocuments.value] = await Promise.all([
      apiRequest<PersonnelFile[]>(query("personnel_file")), apiRequest<NextOfKin[]>(query("next_of_kin")), apiRequest<StaffDocument[]>(query("staff_document")),
    ]);
  } catch (reason) { recordError.value = reason instanceof Error ? reason.message : "Unable to load restricted personnel records"; }
  finally { recordLoading.value = false; }
}
function openRecordForm(kind: typeof recordKind.value) {
  recordKind.value = kind;
  const common = { employee: selectedEmployee.value, company: profile.value?.company || "", classification: "Restricted", retention_category: "Personnel record" };
  recordForm.value = kind === "personnel_file" ? { ...common, file_status: "Active", physical_file_reference: "" }
    : kind === "next_of_kin" ? { ...common, full_name: "", relationship: "", phone: "", is_primary: 0 }
    : { ...common, document_type: "Appointment Letter", verification_status: "Pending" };
  pendingDocument.value = null;
  showRecordForm.value = true;
}
async function saveRestrictedRecord() {
  recordError.value = "";
  try {
    if (recordKind.value === "staff_document") {
      if (!pendingDocument.value) throw new Error("Select a private document to upload");
      const uploaded = await uploadFile(pendingDocument.value, { isPrivate: true });
      recordForm.value.file = uploaded.file_url;
    }
    await apiRequest("/api/method/dtmgp.api.v1.hr.save_restricted_hr_record", { method: "POST", body: JSON.stringify({ record_type: recordKind.value, values: recordForm.value }) });
    showRecordForm.value = false;
    await loadRestrictedRecords(selectedEmployee.value);
  } catch (reason) { recordError.value = reason instanceof Error ? reason.message : "Unable to save restricted personnel record"; }
}
const photoSaving = ref(false);
const photoError = ref("");
const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
async function savePhoto(file: File | null) {
  if (!profile.value) return;
  photoError.value = "";
  if (file && !PHOTO_TYPES.includes(file.type)) { photoError.value = "Choose a JPG, PNG or WebP image"; return; }
  photoSaving.value = true;
  try {
    // Private + attached to the Employee: the file inherits the Employee's LGA-scoped read permission.
    const fileUrl = file ? (await uploadFile(file, { doctype: "Employee", docname: profile.value.name, isPrivate: true })).file_url : null;
    const result = await apiRequest<{ image: string | null }>("/api/method/dtmgp.api.v1.people.set_employee_image", { method: "POST", body: JSON.stringify({ employee: profile.value.name, file_url: fileUrl }) });
    profile.value.image = result.image;
    emit("photo-changed");
  } catch (reason) { photoError.value = reason instanceof Error ? reason.message : "Unable to update the photo"; }
  finally { photoSaving.value = false; }
}
function onEmployeeSaved(result: { name: string; employee_name: string; changed: string[] }) {
  editingEmployee.value = null;
  savedNotice.value = result.changed.length ? `${result.employee_name} updated (${result.changed.length} field${result.changed.length === 1 ? "" : "s"}).` : "";
  emit("employee-saved");
  if (profile.value?.name === result.name) loadProfile(result.name);
}
watch(selectedEmployee, (employee) => { loadProfile(employee); loadRestrictedRecords(employee); if (employee && DOCUMENT_ITEMS.has(activeItem.value)) ensureDocuments(employee); });
watch(activeItem, (item) => { if (selectedEmployee.value && DOCUMENT_ITEMS.has(item)) ensureDocuments(selectedEmployee.value); });

const showPicker = computed(() => PROFILE_ITEMS.has(activeItem.value));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'staff-directory'">
    <form class="directory-toolbar" @submit.prevent="$emit('apply-filters')"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search name, ID or designation" /></label><select v-model="department" class="toolbar-select"><option value="">All departments</option><option v-for="item in departmentOptions" :key="item">{{ item }}</option></select><button class="secondary-action">Apply</button></form>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Grade</th><th>Employment</th><th>Verification</th><th></th></tr></thead><tbody>
      <tr v-for="person in employees" :key="person.name" v-record="{ doctype: 'Employee', name: person.name }"><td><div class="staff-person"><EmployeeAvatar :name="person.employee_name" :image="person.image" /><div><strong>{{ person.employee_name }}</strong><small>{{ person.name }} · {{ person.designation || "No designation" }}</small></div></div></td><td>{{ person.department || "Unassigned" }}</td><td>{{ person.dtmgp_grade_level || "-" }}</td><td><span class="table-status" :class="person.status === 'Active' ? 'success' : 'neutral'">{{ person.status }}</span></td><td><span class="verification-status" :class="person.dtmgp_verification_status === 'Verified' ? 'verified' : 'pending'">{{ person.dtmgp_verification_status || "Pending" }}</span></td><td><button v-if="canManage" class="icon-button" title="Edit employee" @click="editingEmployee = person.name"><Pencil :size="17" /></button></td></tr>
    </tbody></table><footer class="table-footer"><span>Showing {{ employees.length }} of {{ total }} staff</span><div><button :disabled="page === 1" @click="$emit('change-page', -1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * pageSize >= total" @click="$emit('change-page', 1)">Next <ChevronRight :size="14" /></button></div></footer></div>
  </template>

  <template v-else-if="showPicker">
    <div class="directory-toolbar"><label style="flex:1;max-width:360px">Staff member<select v-model="selectedEmployee"><option value="">Select a staff member</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }} — {{ item.name }}</option></select></label></div>
    <p v-if="!selectedEmployee" class="users-empty">Select a staff member above to view their record.</p>
    <p v-else-if="profileLoading" class="users-empty">Loading record...</p>
    <p v-else-if="profileError" class="login-error" role="alert">{{ profileError }}</p>
    <p v-if="recordError" class="login-error" role="alert">{{ recordError }}</p>

    <template v-else-if="profile && activeItem === 'staff-profiles'">
      <div class="employee-photo-panel">
        <EmployeeAvatar :name="profile.employee_name" :image="profile.image" large />
        <div>
          <strong>{{ profile.employee_name }}</strong>
          <small>{{ profile.name }} · {{ profile.designation || "No designation" }}</small>
          <div v-if="canManage" class="employee-photo-actions">
            <button type="button" class="primary-action" @click="editingEmployee = profile.name"><Pencil :size="15" /> Edit details</button>
            <label class="secondary-action" :aria-disabled="photoSaving"><Camera :size="15" /> {{ photoSaving ? "Saving..." : profile.image ? "Change photo" : "Upload photo" }}<input type="file" accept="image/jpeg,image/png,image/webp" hidden :disabled="photoSaving" @change="savePhoto(($event.target as HTMLInputElement).files?.[0] || null); ($event.target as HTMLInputElement).value = ''" /></label>
            <button v-if="profile.image" type="button" class="secondary-action" :disabled="photoSaving" @click="savePhoto(null)"><Trash2 :size="15" /> Remove</button>
          </div>
          <p v-if="photoError" class="login-error" role="alert">{{ photoError }}</p>
        </div>
      </div>
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
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Personnel file</h3><button v-if="canManage && !personnelFiles.length" class="primary-action" @click="openRecordForm('personnel_file')"><Plus :size="15" /> Open file</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Reference</th><th>Status</th><th>Classification</th><th>Retention</th><th>Review</th></tr></thead><tbody><tr v-for="row in personnelFiles" :key="row.name" v-record="{ doctype: 'DTMGP Personnel File', name: row.name }"><td>{{ row.physical_file_reference || row.name }}</td><td>{{ row.file_status }}</td><td>{{ row.classification }}</td><td>{{ row.retention_category }}</td><td>{{ row.retention_review_date || '-' }}</td></tr></tbody></table><p v-if="recordLoading" class="users-empty">Loading personnel file...</p><p v-else-if="!personnelFiles.length" class="users-empty">No digital personnel file has been opened.</p></div>
    </template>

    <template v-else-if="profile && activeItem === 'employment-history'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Internal postings</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>Designation</th><th>Branch</th><th>From</th><th>To</th></tr></thead><tbody><tr v-for="(row, index) in profile.internal_work_history" :key="index"><td>{{ row.department || '-' }}</td><td>{{ row.designation || '-' }}</td><td>{{ row.branch || '-' }}</td><td>{{ row.from_date || '-' }}</td><td>{{ row.to_date || '-' }}</td></tr></tbody></table><p v-if="!profile.internal_work_history.length" class="users-empty">No internal posting history recorded.</p></div>
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">External experience</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Organisation</th><th>Designation</th><th>Contact</th><th>Experience (years)</th></tr></thead><tbody><tr v-for="(row, index) in profile.external_work_history" :key="index"><td>{{ row.company_name || '-' }}</td><td>{{ row.designation || '-' }}</td><td>{{ row.contact || '-' }}</td><td>{{ row.total_experience ?? '-' }}</td></tr></tbody></table><p v-if="!profile.external_work_history.length" class="users-empty">No external experience recorded.</p></div>
    </template>

    <template v-else-if="profile && activeItem === 'next-of-kin'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Next of kin</h3><button v-if="canManage" class="primary-action" @click="openRecordForm('next_of_kin')"><Plus :size="15" /> Add contact</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Name</th><th>Relationship</th><th>Phone</th><th>Email</th><th>Primary</th><th>Verified</th></tr></thead><tbody><tr v-for="row in nextOfKin" :key="row.name" v-record="{ doctype: 'DTMGP Next of Kin', name: row.name }"><td>{{ row.full_name }}</td><td>{{ row.relationship }}</td><td>{{ row.phone }}</td><td>{{ row.email || '-' }}</td><td>{{ row.is_primary ? 'Yes' : 'No' }}</td><td>{{ row.verified_on || '-' }}</td></tr></tbody></table><p v-if="!nextOfKin.length" class="users-empty">No next-of-kin contacts recorded.</p></div>
    </template>

    <template v-else-if="activeItem === 'staff-documents'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Restricted documents</h3><button v-if="canManage" class="primary-action" @click="openRecordForm('staff_document')"><FilePlus2 :size="15" /> Add document</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Type</th><th>Reference</th><th>Classification</th><th>Retention</th><th>Status</th><th>File</th></tr></thead><tbody><tr v-for="row in staffDocuments" :key="row.name" v-record="{ doctype: 'DTMGP Staff Document', name: row.name }"><td>{{ row.document_type }}</td><td>{{ row.reference_number || '-' }}</td><td>{{ row.classification }}</td><td>{{ row.retention_category }}</td><td>{{ row.verification_status }}</td><td><a :href="row.file" target="_blank" rel="noopener">Open private file</a></td></tr></tbody></table><p v-if="!staffDocuments.length" class="users-empty">No restricted staff documents recorded.</p></div>
    </template>
  </template>

  <div v-if="showRecordForm" class="modal-backdrop" @click.self="showRecordForm = false"><form class="user-modal" @submit.prevent="saveRestrictedRecord"><h2>{{ recordKind === 'personnel_file' ? 'Open personnel file' : recordKind === 'next_of_kin' ? 'Add next of kin' : 'Add staff document' }}</h2>
    <template v-if="recordKind === 'personnel_file'"><label>Physical file reference<input v-model="recordForm.physical_file_reference" /></label><label>Status<select v-model="recordForm.file_status"><option>Active</option><option>Closed</option><option>Archived</option><option>Legal Hold</option></select></label></template>
    <template v-else-if="recordKind === 'next_of_kin'"><label>Full name<input v-model="recordForm.full_name" required /></label><label>Relationship<input v-model="recordForm.relationship" required /></label><label>Phone<input v-model="recordForm.phone" required /></label><label>Email<input v-model="recordForm.email" type="email" /></label><label><input v-model="recordForm.is_primary" type="checkbox" :true-value="1" :false-value="0" /> Primary contact</label></template>
    <template v-else><label>Document type<select v-model="recordForm.document_type"><option>Appointment Letter</option><option>Promotion Letter</option><option>Qualification</option><option>Identity Document</option><option>Medical Record</option><option>Disciplinary Record</option><option>Pension Record</option><option>Exit Document</option><option>Other</option></select></label><label>Reference number<input v-model="recordForm.reference_number" /></label><label>Private file<input type="file" required @change="pendingDocument = ($event.target as HTMLInputElement).files?.[0] || null" /></label></template>
    <label v-if="recordKind !== 'next_of_kin'">Classification<select v-model="recordForm.classification"><option>Restricted</option><option>Confidential</option></select></label><label v-if="recordKind !== 'next_of_kin'">Retention category<input v-model="recordForm.retention_category" required /></label><label v-if="recordKind !== 'next_of_kin'">Retention review date<input v-model="recordForm.retention_review_date" type="date" /></label>
    <footer><button type="button" class="secondary-action" @click="showRecordForm = false">Cancel</button><button class="primary-action">Save</button></footer></form></div>
  <p v-if="savedNotice" class="employee-saved-notice" role="status">{{ savedNotice }}</p>
  <EmployeeEditModal v-if="editingEmployee" :employee="editingEmployee" :options="formOptions" @close="editingEmployee = null" @saved="onEmployeeSaved" />
</template>
