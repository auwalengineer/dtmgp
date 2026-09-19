<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Leave, LeaveBalance } from "./types";

interface CalendarRow { employee_name: string; leave_type: string; from_date: string; to_date: string }
interface OnLeaveRow { employee_name: string; leave_type: string; to_date: string }

const props = defineProps<{ leave: Leave[]; leaveBalances: LeaveBalance[]; canManage: boolean }>();
defineEmits<{ "decide-leave": [name: string, decision: "Approved" | "Rejected"] }>();

const ITEM_LABELS: Record<string, string> = { "leave-requests": "Leave Requests", "leave-approvals": "Leave Approvals", "leave-balances": "Leave Balances", "leave-calendar": "Leave Calendar", "staff-on-leave": "Staff on Leave" };
const DEFAULT_ITEM = "leave-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const pendingLeave = computed(() => props.leave.filter((item) => item.status === "Open" || item.status === "Draft"));
const calendarRows = ref<CalendarRow[]>([]);
const onLeaveRows = ref<OnLeaveRow[]>([]);
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
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>From</th><th>To</th></tr></thead><tbody><tr v-for="(row, index) in calendarRows" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.leave_type }}</td><td>{{ row.from_date }}</td><td>{{ row.to_date }}</td></tr></tbody></table><p v-if="!calendarRows.length" class="users-empty">A month-view leave calendar will appear here once connected.</p></div>
  </template>

  <template v-else-if="activeItem === 'staff-on-leave'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Leave type</th><th>Returns</th></tr></thead><tbody><tr v-for="(row, index) in onLeaveRows" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.leave_type }}</td><td>{{ row.to_date }}</td></tr></tbody></table><p v-if="!onLeaveRows.length" class="users-empty">Staff currently on leave will appear here once connected; the workforce summary above shows a same-day count only.</p></div>
  </template>
</template>
