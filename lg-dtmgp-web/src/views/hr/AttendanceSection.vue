<script setup lang="ts">
import { CalendarClock, CalendarDays, CircleAlert } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import type { AttendanceItem, AttendanceSummary } from "./types";

interface ShiftAssignmentRow { employee_name: string; shift_type: string; start_date: string; end_date: string | null }
interface AttendanceReportRow { period: string; present: number; absent: number; on_leave: number; late_entries: number }

const props = defineProps<{ attendanceSummary: AttendanceSummary | null; attendanceItems: AttendanceItem[] }>();

const ITEM_LABELS: Record<string, string> = { "attendance-records": "Attendance Records", "shift-assignments": "Shift Assignments", "late-arrivals": "Late Arrivals", "absent-staff": "Absent Staff", "attendance-reports": "Attendance Reports" };
const DEFAULT_ITEM = "attendance-records";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const lateArrivals = computed(() => props.attendanceItems.filter((item) => item.late_entry));
const absentStaff = computed(() => props.attendanceItems.filter((item) => item.status === "Absent"));
const shiftAssignments = ref<ShiftAssignmentRow[]>([]);
const attendanceReports = ref<AttendanceReportRow[]>([]);
const reportFrom = ref("");
const reportTo = ref("");
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'attendance-records'">
    <section class="hr-metrics" aria-label="Attendance today" v-if="attendanceSummary">
      <article><span class="hr-metric-icon green"><CalendarClock :size="19" /></span><div><small>Present today</small><strong>{{ attendanceSummary.present }}</strong><p>{{ attendanceSummary.date }}</p></div></article>
      <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Absent</small><strong>{{ attendanceSummary.absent }}</strong><p>{{ attendanceSummary.late_entries }} late entries</p></div></article>
      <article><span class="hr-metric-icon gold"><CalendarDays :size="19" /></span><div><small>On leave</small><strong>{{ attendanceSummary.on_leave }}</strong><p>Half day: {{ attendanceSummary.half_day }}</p></div></article>
    </section>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th><th>Status</th><th>Late</th></tr></thead><tbody><tr v-for="item in attendanceItems" :key="item.name" v-record="{ doctype: 'Attendance', name: item.name }"><td>{{ item.employee_name }}</td><td>{{ item.attendance_date }}</td><td><span class="table-status" :class="item.status === 'Present' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.late_entry ? 'Yes' : 'No' }}</td></tr></tbody></table><p v-if="!attendanceItems.length" class="users-empty">No attendance recorded for today.</p></div>
  </template>

  <template v-else-if="activeItem === 'late-arrivals'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th><th>Status</th></tr></thead><tbody><tr v-for="item in lateArrivals" :key="item.name" v-record="{ doctype: 'Attendance', name: item.name }"><td>{{ item.employee_name }}</td><td>{{ item.attendance_date }}</td><td><span class="table-status neutral">{{ item.status }}</span></td></tr></tbody></table><p v-if="!lateArrivals.length" class="users-empty">No late arrivals recorded for today.</p></div>
  </template>

  <template v-else-if="activeItem === 'absent-staff'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th></tr></thead><tbody><tr v-for="item in absentStaff" :key="item.name" v-record="{ doctype: 'Attendance', name: item.name }"><td>{{ item.employee_name }}</td><td>{{ item.attendance_date }}</td></tr></tbody></table><p v-if="!absentStaff.length" class="users-empty">No absences recorded for today.</p></div>
  </template>

  <template v-else-if="activeItem === 'shift-assignments'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Shift</th><th>Start date</th><th>End date</th></tr></thead><tbody><tr v-for="(row, index) in shiftAssignments" :key="index"><td>{{ row.employee_name }}</td><td>{{ row.shift_type }}</td><td>{{ row.start_date }}</td><td>{{ row.end_date || "-" }}</td></tr></tbody></table><p v-if="!shiftAssignments.length" class="users-empty">Shift assignments will appear here once a shift-assignment service is available for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'attendance-reports'">
    <div class="directory-toolbar"><label>From<input v-model="reportFrom" type="date" /></label><label>To<input v-model="reportTo" type="date" /></label></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Period</th><th>Present</th><th>Absent</th><th>On leave</th><th>Late entries</th></tr></thead><tbody><tr v-for="(row, index) in attendanceReports" :key="index"><td>{{ row.period }}</td><td>{{ row.present }}</td><td>{{ row.absent }}</td><td>{{ row.on_leave }}</td><td>{{ row.late_entries }}</td></tr></tbody></table><p v-if="!attendanceReports.length" class="users-empty">Attendance trend reports across a date range aren't available yet; see Attendance Records for today's snapshot.</p></div>
  </template>
</template>
