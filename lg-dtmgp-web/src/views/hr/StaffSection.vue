<script setup lang="ts">
import { ChevronLeft, ChevronRight, Pencil, Search } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Employee } from "./types";
import { initials } from "./types";

interface ProfileRow { employee_name: string; department: string | null; designation: string | null; dtmgp_grade_level: string; status: string }
interface PersonnelFileRow { employee_name: string; department: string | null; document_count: number }
interface EmploymentHistoryRow { employee_name: string; department: string | null; designation: string | null; from_date: string; to_date: string }
interface NextOfKinRow { employee_name: string; person_to_be_contacted: string; relation: string; emergency_phone_number: string }
interface StaffDocumentRow { file_name: string; employee_name: string; is_private: number; creation: string }

defineProps<{ employees: Employee[]; total: number; page: number; pageSize: number; departmentOptions: string[]; canManage: boolean }>();
const search = defineModel<string>("search", { required: true });
const department = defineModel<string>("department", { required: true });
defineEmits<{ "apply-filters": []; "change-page": [change: number]; "edit-employee": [employee: Employee] }>();

const ITEM_LABELS: Record<string, string> = { "staff-directory": "Staff Directory", "staff-profiles": "Staff Profiles", "digital-personnel-files": "Digital Personnel Files", "employment-history": "Employment History", "next-of-kin": "Next of Kin", "staff-documents": "Staff Documents" };
const DEFAULT_ITEM = "staff-directory";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const staffProfiles = ref<ProfileRow[]>([]);
const personnelFiles = ref<PersonnelFileRow[]>([]);
const employmentHistory = ref<EmploymentHistoryRow[]>([]);
const nextOfKin = ref<NextOfKinRow[]>([]);
const staffDocuments = ref<StaffDocumentRow[]>([]);
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'staff-directory'">
    <form class="directory-toolbar" @submit.prevent="$emit('apply-filters')"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search name, ID or designation" /></label><select v-model="department" class="toolbar-select"><option value="">All departments</option><option v-for="item in departmentOptions" :key="item">{{ item }}</option></select><button class="secondary-action">Apply</button></form>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Grade</th><th>Employment</th><th>Verification</th><th></th></tr></thead><tbody>
      <tr v-for="person in employees" :key="person.name"><td><div class="staff-person"><span>{{ initials(person.employee_name) }}</span><div><strong>{{ person.employee_name }}</strong><small>{{ person.name }} · {{ person.designation || "No designation" }}</small></div></div></td><td>{{ person.department || "Unassigned" }}</td><td>{{ person.dtmgp_grade_level || "-" }}</td><td><span class="table-status" :class="person.status === 'Active' ? 'success' : 'neutral'">{{ person.status }}</span></td><td><span class="verification-status" :class="person.dtmgp_verification_status === 'Verified' ? 'verified' : 'pending'">{{ person.dtmgp_verification_status || "Pending" }}</span></td><td><button v-if="canManage" class="icon-button" title="Edit employee" @click="$emit('edit-employee', person)"><Pencil :size="17" /></button></td></tr>
    </tbody></table><footer class="table-footer"><span>Showing {{ employees.length }} of {{ total }} staff</span><div><button :disabled="page === 1" @click="$emit('change-page', -1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * pageSize >= total" @click="$emit('change-page', 1)">Next <ChevronRight :size="14" /></button></div></footer></div>
  </template>

  <template v-else-if="activeItem === 'staff-profiles'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Designation</th><th>Grade</th><th>Status</th></tr></thead><tbody><tr v-for="row in staffProfiles" :key="row.employee_name"><td>{{ row.employee_name }}</td><td>{{ row.department || "-" }}</td><td>{{ row.designation || "-" }}</td><td>{{ row.dtmgp_grade_level || "-" }}</td><td>{{ row.status }}</td></tr></tbody></table><p v-if="!staffProfiles.length" class="users-empty">Staff profiles will appear here once linked to the employee record service.</p></div>
  </template>

  <template v-else-if="activeItem === 'digital-personnel-files'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Documents on file</th></tr></thead><tbody><tr v-for="row in personnelFiles" :key="row.employee_name"><td>{{ row.employee_name }}</td><td>{{ row.department || "-" }}</td><td>{{ row.document_count }}</td></tr></tbody></table><p v-if="!personnelFiles.length" class="users-empty">Digital personnel files (profile + documents + history bundle) will appear here once connected to each staff member's record.</p></div>
  </template>

  <template v-else-if="activeItem === 'employment-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Designation</th><th>From</th><th>To</th></tr></thead><tbody><tr v-for="(row, index) in employmentHistory" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.department || "-" }}</td><td>{{ row.designation || "-" }}</td><td>{{ row.from_date }}</td><td>{{ row.to_date }}</td></tr></tbody></table><p v-if="!employmentHistory.length" class="users-empty">Internal posting history for each staff member will appear here once connected.</p></div>
  </template>

  <template v-else-if="activeItem === 'next-of-kin'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Contact person</th><th>Relationship</th><th>Phone</th></tr></thead><tbody><tr v-for="(row, index) in nextOfKin" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.person_to_be_contacted }}</td><td>{{ row.relation }}</td><td>{{ row.emergency_phone_number }}</td></tr></tbody></table><p v-if="!nextOfKin.length" class="users-empty">Only a single emergency contact per staff member is currently recorded; a dedicated next-of-kin list is not yet tracked.</p></div>
  </template>

  <template v-else-if="activeItem === 'staff-documents'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Document</th><th>Staff member</th><th>Visibility</th><th>Uploaded</th></tr></thead><tbody><tr v-for="(row, index) in staffDocuments" :key="index"><td>{{ row.file_name }}</td><td>{{ row.employee_name }}</td><td>{{ row.is_private ? "Private" : "Public" }}</td><td>{{ row.creation }}</td></tr></tbody></table><p v-if="!staffDocuments.length" class="users-empty">No documents on file. Document uploads will connect to each staff member's record in a later phase.</p></div>
  </template>
</template>
