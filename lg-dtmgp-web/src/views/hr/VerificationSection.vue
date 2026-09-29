<script setup lang="ts">
import { BarChart3, CircleCheck, ShieldAlert } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { Exercise, VerificationRecord } from "./types";

const props = defineProps<{ exercises: Exercise[]; activeExercise: string; verificationRecords: VerificationRecord[]; canManage: boolean }>();
defineEmits<{ "new-exercise": []; "select-exercise": [name: string]; "transition-exercise": [name: string, target: string]; "new-record": []; "review-record": [name: string, status: "Verified" | "Exception"] }>();

const ITEM_LABELS: Record<string, string> = { "verification-exercises": "Verification Exercises", "pending-verification": "Pending Verification", "verified-staff": "Verified Staff", "biometric-enrolment": "Biometric Enrolment", "verification-exceptions": "Verification Exceptions", "verification-reports": "Verification Reports" };
const DEFAULT_ITEM = "verification-exercises";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const pendingRecords = computed(() => props.verificationRecords.filter((record) => record.review_status === "Pending"));
const verifiedRecords = computed(() => props.verificationRecords.filter((record) => record.review_status === "Verified"));
const exceptionRecords = computed(() => props.verificationRecords.filter((record) => record.review_status === "Exception"));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'verification-exercises'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Verification exercises</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-exercise')">New exercise</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Title</th><th>Cycle</th><th>Status</th><th></th></tr></thead><tbody>
      <tr v-for="exercise in exercises" :key="exercise.name" :class="{ current: exercise.name === activeExercise }" v-record="{ doctype: 'DTMGP Staff Verification Exercise', name: exercise.name }"><td><a href="#" @click.prevent="$emit('select-exercise', exercise.name)">{{ exercise.title }}</a></td><td>{{ exercise.cycle_start_date }} – {{ exercise.cycle_end_date }}</td><td><span class="table-status" :class="exercise.status === 'Completed' ? 'success' : 'neutral'">{{ exercise.status }}</span></td><td><button v-if="canManage && exercise.status === 'Draft'" class="secondary-action compact-action" @click="$emit('transition-exercise', exercise.name, 'In Progress')">Start</button><button v-if="canManage && exercise.status === 'In Progress'" class="secondary-action compact-action" @click="$emit('transition-exercise', exercise.name, 'Completed')">Complete</button></td></tr>
    </tbody></table><p v-if="!exercises.length" class="users-empty">No verification exercises for this LGA yet.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Verification records</h3><button v-if="canManage && activeExercise" class="secondary-action" @click="$emit('new-record')">Prepare record</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Prepared by</th><th>Biometric</th><th>Review status</th><th></th></tr></thead><tbody>
      <tr v-for="record in verificationRecords" :key="record.name" v-record="{ doctype: 'DTMGP Staff Verification Record', name: record.name }"><td>{{ record.employee }}</td><td>{{ record.prepared_by }}</td><td>{{ record.biometric_captured ? 'Captured' : 'Pending' }}</td><td><span class="verification-status" :class="record.review_status === 'Verified' ? 'verified' : 'pending'">{{ record.review_status }}</span><small v-if="record.exception_reason"> — {{ record.exception_reason }}</small></td><td v-if="canManage && record.review_status === 'Pending'"><button class="secondary-action compact-action" @click="$emit('review-record', record.name, 'Verified')"><CircleCheck :size="14" /> Verify</button> <button class="secondary-action compact-action" @click="$emit('review-record', record.name, 'Exception')"><ShieldAlert :size="14" /> Exception</button></td><td v-else></td></tr>
    </tbody></table><p v-if="!verificationRecords.length" class="users-empty">No verification records for this exercise.</p></div>
  </template>

  <template v-else-if="activeItem === 'pending-verification'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Prepared by</th><th>Biometric</th><th></th></tr></thead><tbody><tr v-for="record in pendingRecords" :key="record.name" v-record="{ doctype: 'DTMGP Staff Verification Record', name: record.name }"><td>{{ record.employee }}</td><td>{{ record.prepared_by }}</td><td>{{ record.biometric_captured ? 'Captured' : 'Pending' }}</td><td v-if="canManage"><button class="secondary-action compact-action" @click="$emit('review-record', record.name, 'Verified')"><CircleCheck :size="14" /> Verify</button> <button class="secondary-action compact-action" @click="$emit('review-record', record.name, 'Exception')"><ShieldAlert :size="14" /> Exception</button></td></tr></tbody></table><p v-if="!pendingRecords.length" class="users-empty">No records awaiting verification for this exercise.</p></div>
  </template>

  <template v-else-if="activeItem === 'verified-staff'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Reviewed by</th></tr></thead><tbody><tr v-for="record in verifiedRecords" :key="record.name" v-record="{ doctype: 'DTMGP Staff Verification Record', name: record.name }"><td>{{ record.employee }}</td><td>{{ record.reviewed_by || "-" }}</td></tr></tbody></table><p v-if="!verifiedRecords.length" class="users-empty">No verified staff for this exercise yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'biometric-enrolment'">
    <p class="users-empty" style="text-align:left;padding:12px 20px 0">Biometric enrolment is currently a manual confirmation flag on the verification record; a device-linked enrolment workflow isn't available yet.</p>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Prepared by</th><th>Biometric</th></tr></thead><tbody><tr v-for="record in verificationRecords" :key="record.name" v-record="{ doctype: 'DTMGP Staff Verification Record', name: record.name }"><td>{{ record.employee }}</td><td>{{ record.prepared_by }}</td><td><span class="table-status" :class="record.biometric_captured ? 'success' : 'neutral'">{{ record.biometric_captured ? 'Captured' : 'Pending' }}</span></td></tr></tbody></table><p v-if="!verificationRecords.length" class="users-empty">No verification records for this exercise.</p></div>
  </template>

  <template v-else-if="activeItem === 'verification-exceptions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Reason</th></tr></thead><tbody><tr v-for="record in exceptionRecords" :key="record.name" v-record="{ doctype: 'DTMGP Staff Verification Record', name: record.name }"><td>{{ record.employee }}</td><td>{{ record.exception_reason || "-" }}</td></tr></tbody></table><p v-if="!exceptionRecords.length" class="users-empty">No verification exceptions for this exercise.</p></div>
  </template>

  <template v-else-if="activeItem === 'verification-reports'">
    <PreviewCard :icon="BarChart3" title="Verification reports" body="Aggregate verification statistics (by status, exercise and LGA) aren't available yet — review Pending, Verified and Exception views above for current-exercise detail." />
  </template>
</template>
