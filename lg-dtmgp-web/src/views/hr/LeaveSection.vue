<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Leave, LeaveBalance } from "./types";

interface CalendarRow { name: string; employee: string; employee_name: string; leave_type: string; from_date: string; to_date: string; status: string }

const CALENDAR_ITEMS = new Set(["leave-calendar", "staff-on-leave"]);
const props = defineProps<{ leave: Leave[]; leaveBalances: LeaveBalance[]; canManage: boolean }>();
defineEmits<{ "decide-leave": [name: string, decision: "Approved" | "Rejected"] }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "leave-requests": "Leave Requests", "leave-approvals": "Leave Approvals", "leave-balances": "Leave Balances", "leave-calendar": "Leave Calendar", "staff-on-leave": "Staff on Leave" };
const DEFAULT_ITEM = "leave-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const pendingLeave = computed(() => props.leave.filter((item) => item.status === "Open" || item.status === "Draft"));
const calendarRows = ref<CalendarRow[]>([]);
const calendarLoading = ref(false);
const calendarLoaded = ref(false);
async function loadCalendar() {
  if (calendarLoaded.value) return;
  calendarLoading.value = true;
  try { calendarRows.value = await apiRequest<CalendarRow[]>(`/api/method/dtmgp.api.v1.hr.list_leave_calendar?company=${encodeURIComponent(session.activeLga)}`); calendarLoaded.value = true; }
  finally { calendarLoading.value = false; }
}
watch(activeItem, (item) => { if (CALENDAR_ITEMS.has(item)) loadCalendar(); }, { immediate: true });

function today() { return new Date().toISOString().slice(0, 10); }
const onLeaveToday = computed(() => calendarRows.value.filter((row) => row.from_date <= today() && row.to_date >= today()));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'leave-requests'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>From</th><th>To</th><th>Days</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in leave" :key="item.name"><td>{{ item.employee_name }}</td><td>{{ item.leave_type }}</td><td>{{ item.from_date }}</td><td>{{ item.to_date }}</td><td>{{ item.total_leave_days }}</td><td><span class="table-status" :class="item.status === 'Approved' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><template v-if="canManage && (item.status === 'Open' || item.status === 'Draft')"><button class="secondary-action compact-action" @click="$emit('decide-leave', item.name, 'Approved')">Approve</button> <button class="secondary-action compact-action" @click="$emit('decide-leave', item.name, 'Rejected')">Reject</button></template></td></tr></tbody></table><p v-if="!leave.length" class="users-empty">No leave applications in this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'leave-approvals'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>From</th><th>To</th><th>Days</th><th></th></tr></thead><tbody><tr v-for="item in pendingLeave" :key="item.name"><td>{{ item.employee_name }}</td><td>{{ item.leave_type }}</td><td>{{ item.from_date }}</td><td>{{ item.to_date }}</td><td>{{ item.total_leave_days }}</td><td v-if="canManage"><button class="secondary-action compact-action" @click="$emit('decide-leave', item.name, 'Approved')">Approve</button> <button class="secondary-action compact-action" @click="$emit('decide-leave', item.name, 'Rejected')">Reject</button></td></tr></tbody></table><p v-if="!pendingLeave.length" class="users-empty">No leave applications awaiting a decision.</p></div>
  </template>

  <template v-else-if="activeItem === 'leave-balances'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>Allocated</th><th>Taken</th><th>Balance</th></tr></thead><tbody><tr v-for="row in leaveBalances" :key="row.employee + row.leave_type"><td>{{ row.employee_name }}</td><td>{{ row.leave_type }}</td><td>{{ row.total_leaves_allocated }}</td><td>{{ row.taken }}</td><td>{{ row.balance }}</td></tr></tbody></table><p v-if="!leaveBalances.length" class="users-empty">No leave allocations recorded.</p></div>
  </template>

  <template v-else-if="activeItem === 'leave-calendar'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>From</th><th>To</th></tr></thead><tbody><tr v-for="row in calendarRows" :key="row.name"><td>{{ row.employee_name }}</td><td>{{ row.leave_type }}</td><td>{{ row.from_date }}</td><td>{{ row.to_date }}</td></tr></tbody></table><p v-if="calendarLoading" class="users-empty">Loading this month's leave calendar...</p><p v-else-if="!calendarRows.length" class="users-empty">No approved leave overlapping this month.</p></div>
  </template>

  <template v-else-if="activeItem === 'staff-on-leave'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>Returns</th></tr></thead><tbody><tr v-for="row in onLeaveToday" :key="row.name"><td>{{ row.employee_name }}</td><td>{{ row.leave_type }}</td><td>{{ row.to_date }}</td></tr></tbody></table><p v-if="calendarLoading" class="users-empty">Loading...</p><p v-else-if="!onLeaveToday.length" class="users-empty">No staff currently on approved leave.</p></div>
  </template>
</template>
