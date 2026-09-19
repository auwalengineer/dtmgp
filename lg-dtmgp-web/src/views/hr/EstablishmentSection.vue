<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import { docstatusLabel } from "./types";
import type { Department, Position, StaffingPlan } from "./types";

const props = defineProps<{ staffingPlans: StaffingPlan[]; positions: Position[]; departments: Department[]; canManage: boolean }>();
defineEmits<{ "new-staffing-plan": []; "submit-staffing-plan": [name: string] }>();

const ITEM_LABELS: Record<string, string> = { "approved-establishment": "Approved Establishment", "establishment-positions": "Establishment Positions", "vacant-positions": "Vacant Positions", "occupied-positions": "Occupied Positions", overstaffing: "Overstaffing", "staffing-shortages": "Staffing Shortages" };
const DEFAULT_ITEM = "approved-establishment";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const vacantPositions = computed(() => props.positions.filter((position) => position.position_status === "Vacant"));
const occupiedPositions = computed(() => props.positions.filter((position) => position.position_status === "Filled" || position.position_status === "Partially Filled"));
const overstaffedPositions = computed(() => props.positions.filter((position) => position.position_status === "Overstaffed"));
const staffingShortages = computed(() => [...props.positions].filter((position) => position.vacancies > 0).sort((a, b) => b.vacancies - a.vacancies));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'approved-establishment'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Staffing plans</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-staffing-plan')">New staffing plan</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>Period</th><th>Est. budget</th><th>Status</th><th></th></tr></thead><tbody>
      <tr v-for="plan in staffingPlans" :key="plan.name"><td>{{ plan.department || '-' }}</td><td>{{ plan.from_date }} – {{ plan.to_date }}</td><td>{{ plan.total_estimated_budget }}</td><td><span class="table-status" :class="plan.docstatus === 1 ? 'success' : 'neutral'">{{ docstatusLabel(plan.docstatus, 'Approved') }}</span></td><td><button v-if="canManage && plan.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-staffing-plan', plan.name)">Approve</button></td></tr>
    </tbody></table><p v-if="!staffingPlans.length" class="users-empty">No staffing plans defined yet.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Approved positions</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Approved</th><th>Filled</th><th>Vacancies</th><th>Status</th></tr></thead><tbody>
      <tr v-for="position in positions" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.number_of_positions }}</td><td>{{ position.current_count }}</td><td>{{ position.vacancies }}</td><td><span class="table-status" :class="position.position_status === 'Filled' ? 'success' : 'neutral'">{{ position.position_status }}</span></td></tr>
    </tbody></table><p v-if="!positions.length" class="users-empty">No approved staffing plan yet — positions appear once one is approved.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Department headcount</h3></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>LGA</th><th>Active employees</th></tr></thead><tbody><tr v-for="item in departments" :key="item.name"><td>{{ item.department_name }}</td><td>{{ item.company.replace(' Local Government Area', ' LGA') }}</td><td>{{ item.employee_count }}</td></tr></tbody></table><p v-if="!departments.length" class="users-empty">No departments configured for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'establishment-positions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Approved</th><th>Filled</th><th>Vacancies</th><th>Status</th></tr></thead><tbody><tr v-for="position in positions" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.number_of_positions }}</td><td>{{ position.current_count }}</td><td>{{ position.vacancies }}</td><td><span class="table-status" :class="position.position_status === 'Filled' ? 'success' : 'neutral'">{{ position.position_status }}</span></td></tr></tbody></table><p v-if="!positions.length" class="users-empty">No approved staffing plan yet — positions appear once one is approved.</p></div>
  </template>

  <template v-else-if="activeItem === 'vacant-positions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Approved</th><th>Vacancies</th></tr></thead><tbody><tr v-for="position in vacantPositions" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.number_of_positions }}</td><td>{{ position.vacancies }}</td></tr></tbody></table><p v-if="!vacantPositions.length" class="users-empty">No vacant positions in the approved establishment.</p></div>
  </template>

  <template v-else-if="activeItem === 'occupied-positions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Approved</th><th>Filled</th><th>Status</th></tr></thead><tbody><tr v-for="position in occupiedPositions" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.number_of_positions }}</td><td>{{ position.current_count }}</td><td><span class="table-status success">{{ position.position_status }}</span></td></tr></tbody></table><p v-if="!occupiedPositions.length" class="users-empty">No occupied positions in the approved establishment.</p></div>
  </template>

  <template v-else-if="activeItem === 'overstaffing'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Approved</th><th>Filled</th><th>Excess</th></tr></thead><tbody><tr v-for="position in overstaffedPositions" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.number_of_positions }}</td><td>{{ position.current_count }}</td><td>{{ position.current_count - position.number_of_positions }}</td></tr></tbody></table><p v-if="!overstaffedPositions.length" class="users-empty">No overstaffed designations in the approved establishment.</p></div>
  </template>

  <template v-else-if="activeItem === 'staffing-shortages'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Vacancies</th><th>Status</th></tr></thead><tbody><tr v-for="position in staffingShortages" :key="position.parent + position.designation"><td>{{ position.designation }}</td><td>{{ position.vacancies }}</td><td><span class="table-status neutral">{{ position.position_status }}</span></td></tr></tbody></table><p v-if="!staffingShortages.length" class="users-empty">No staffing shortages against the approved establishment.</p></div>
  </template>
</template>
