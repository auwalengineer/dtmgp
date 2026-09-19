<script setup lang="ts">
import { LogOut } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { RetirementItem, Separation } from "./types";

interface FormerStaffRow { employee_name: string; department: string | null; relieving_date: string | null; reason: string | null }

const props = defineProps<{ retirementForecast: RetirementItem[]; separations: Separation[]; canManage: boolean }>();
defineEmits<{ "new-exit-case": []; "submit-separation": [name: string]; "open-separation-detail": [name: string] }>();

const ITEM_LABELS: Record<string, string> = { "upcoming-retirements": "Upcoming Retirements", "retirement-processing": "Retirement Processing", resignations: "Resignations", terminations: "Terminations", "exit-clearance": "Exit Clearance", "former-staff": "Former Staff" };
const DEFAULT_ITEM = "upcoming-retirements";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const retirementCases = computed(() => props.separations.filter((s) => s.dtmgp_exit_type === "Retirement"));
const resignationCases = computed(() => props.separations.filter((s) => s.dtmgp_exit_type === "Resignation"));
const terminationCases = computed(() => props.separations.filter((s) => s.dtmgp_exit_type === "Termination"));
const formerStaff = ref<FormerStaffRow[]>([]);
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'upcoming-retirements'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Department</th><th>Designation</th><th>Retirement date</th></tr></thead><tbody><tr v-for="item in retirementForecast" :key="item.name"><td>{{ item.employee_name }}</td><td>{{ item.department || '-' }}</td><td>{{ item.designation || '-' }}</td><td>{{ item.date_of_retirement }}</td></tr></tbody></table><p v-if="!retirementForecast.length" class="users-empty">No upcoming retirements in this window.</p></div>
  </template>

  <template v-else-if="activeItem === 'retirement-processing'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Status</th><th>Date</th><th></th></tr></thead><tbody><tr v-for="item in retirementCases" :key="item.name"><td>{{ item.employee_name }}</td><td><span class="table-status" :class="item.boarding_status === 'Completed' ? 'success' : 'neutral'">{{ item.docstatus === 0 ? 'Draft' : item.boarding_status }}</span></td><td>{{ item.resignation_letter_date || '-' }}</td><td><button v-if="canManage && item.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-separation', item.name)">Submit</button><button v-if="item.docstatus === 1" class="secondary-action compact-action" @click="$emit('open-separation-detail', item.name)">Checklist</button></td></tr></tbody></table><p v-if="!retirementCases.length" class="users-empty">No retirement cases recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'resignations'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Status</th><th>Date</th><th></th></tr></thead><tbody><tr v-for="item in resignationCases" :key="item.name"><td>{{ item.employee_name }}</td><td><span class="table-status" :class="item.boarding_status === 'Completed' ? 'success' : 'neutral'">{{ item.docstatus === 0 ? 'Draft' : item.boarding_status }}</span></td><td>{{ item.resignation_letter_date || '-' }}</td><td><button v-if="canManage && item.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-separation', item.name)">Submit</button><button v-if="item.docstatus === 1" class="secondary-action compact-action" @click="$emit('open-separation-detail', item.name)">Checklist</button></td></tr></tbody></table><p v-if="!resignationCases.length" class="users-empty">No resignation cases recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'terminations'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Status</th><th>Date</th><th></th></tr></thead><tbody><tr v-for="item in terminationCases" :key="item.name"><td>{{ item.employee_name }}</td><td><span class="table-status" :class="item.boarding_status === 'Completed' ? 'success' : 'neutral'">{{ item.docstatus === 0 ? 'Draft' : item.boarding_status }}</span></td><td>{{ item.resignation_letter_date || '-' }}</td><td><button v-if="canManage && item.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-separation', item.name)">Submit</button><button v-if="item.docstatus === 1" class="secondary-action compact-action" @click="$emit('open-separation-detail', item.name)">Checklist</button></td></tr></tbody></table><p v-if="!terminationCases.length" class="users-empty">No termination cases recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'exit-clearance'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Exit clearances</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-exit-case')"><LogOut :size="15" /> New exit case</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Status</th><th>Date</th><th></th></tr></thead><tbody><tr v-for="item in separations" :key="item.name"><td>{{ item.employee_name }}</td><td><span class="table-status" :class="item.boarding_status === 'Completed' ? 'success' : 'neutral'">{{ item.docstatus === 0 ? 'Draft' : item.boarding_status }}</span></td><td>{{ item.resignation_letter_date || '-' }}</td><td>
      <button v-if="canManage && item.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-separation', item.name)">Submit</button>
      <button v-if="item.docstatus === 1" class="secondary-action compact-action" @click="$emit('open-separation-detail', item.name)">Checklist</button>
    </td></tr></tbody></table><p v-if="!separations.length" class="users-empty">No exit cases recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'former-staff'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Department</th><th>Relieving date</th><th>Reason</th></tr></thead><tbody><tr v-for="(row, index) in formerStaff" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.department || '-' }}</td><td>{{ row.relieving_date || '-' }}</td><td>{{ row.reason || '-' }}</td></tr></tbody></table><p v-if="!formerStaff.length" class="users-empty">Former staff records will appear here once connected to the employee record service.</p></div>
  </template>
</template>
