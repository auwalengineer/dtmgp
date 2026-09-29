<script setup lang="ts">
import { CloudOff, FilePlus2, WifiOff } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import { mapLink } from "./types";
import type { InspectionRecord } from "./types";

const props = defineProps<{ inspections: InspectionRecord[]; canManage: boolean; offlineQueueCount: number; isOnline: boolean }>();
const emit = defineEmits<{ "new-inspection": []; transition: [name: string, target: string] }>();

const ITEM_LABELS: Record<string, string> = { "inspection-schedule": "Inspection Schedule", "assigned-inspections": "Assigned Inspections", "mobile-inspections": "Mobile Inspections", "inspection-reports": "Inspection Reports", "gps-photo-evidence": "GPS & Photo Evidence", "inspection-exceptions": "Inspection Exceptions" };
const DEFAULT_ITEM = "inspection-schedule";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const scheduled = computed(() => props.inspections.filter((i) => i.status === "Scheduled"));
const assigned = computed(() => props.inspections.filter((i) => ["Scheduled", "In Progress"].includes(i.status) && i.inspector));
const completed = computed(() => props.inspections.filter((i) => i.status === "Completed"));
const geoTagged = computed(() => props.inspections.filter((i) => i.latitude && i.longitude));
const exceptions = computed(() => props.inspections.filter((i) => i.status === "Exception"));

const NEXT_ACTIONS: Record<string, { label: string; target: string }[]> = {
  Scheduled: [{ label: "Start", target: "In Progress" }, { label: "Log exception", target: "Exception" }],
  "In Progress": [{ label: "Mark completed", target: "Completed" }, { label: "Log exception", target: "Exception" }],
};
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <div v-if="activeItem !== 'mobile-inspections'" class="directory-toolbar"><h3 style="margin:0;flex:1">{{ ITEM_LABELS[activeItem] }}</h3><button v-if="canManage" class="secondary-action" @click="emit('new-inspection')"><FilePlus2 :size="15" /> New inspection</button></div>

  <template v-if="activeItem === 'inspection-schedule'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Scheduled date</th><th>Inspector</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in scheduled" :key="item.name" v-record="{ doctype: 'DTMGP Project Inspection', name: item.name }"><td><strong>{{ item.project }}</strong></td><td>{{ item.scheduled_date }}</td><td>{{ item.inspector || 'Unassigned' }}</td><td v-if="canManage"><button v-for="action in NEXT_ACTIONS[item.status] || []" :key="action.target" class="secondary-action compact-action" style="margin:2px" @click="emit('transition', item.name, action.target)">{{ action.label }}</button></td></tr></tbody></table><p v-if="!scheduled.length" class="users-empty">No inspections scheduled for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'assigned-inspections'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Inspector</th><th>Status</th><th>Scheduled date</th></tr></thead><tbody><tr v-for="item in assigned" :key="item.name" v-record="{ doctype: 'DTMGP Project Inspection', name: item.name }"><td><strong>{{ item.project }}</strong></td><td>{{ item.inspector }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td>{{ item.scheduled_date }}</td></tr></tbody></table><p v-if="!assigned.length" class="users-empty">No inspections currently assigned to an inspector.</p></div>
  </template>

  <template v-else-if="activeItem === 'mobile-inspections'">
    <p class="users-empty" style="text-align:left;padding:0 20px">The "New inspection" form under Inspection Schedule is the mobile capture flow — it works on a phone browser and includes GPS coordinates and a photo upload. When the device is offline, entries are queued on-device (IndexedDB) and synced automatically the next time the connection returns.</p>
    <div class="finance-metrics" aria-label="Offline capture status">
      <article><span class="hr-metric-icon" :class="isOnline ? 'green' : 'red'"><WifiOff :size="19" /></span><div><small>Connection</small><strong>{{ isOnline ? 'Online' : 'Offline' }}</strong><p>{{ isOnline ? 'Inspections save directly' : 'New inspections are being queued on this device' }}</p></div></article>
      <article><span class="hr-metric-icon" :class="offlineQueueCount ? 'gold' : 'blue'"><CloudOff :size="19" /></span><div><small>Queued inspections</small><strong>{{ offlineQueueCount }}</strong><p>{{ offlineQueueCount ? 'Will sync automatically when back online' : 'Nothing waiting to sync' }}</p></div></article>
    </div>
  </template>

  <template v-else-if="activeItem === 'inspection-reports'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Scheduled date</th><th>Findings</th><th>Recommendation</th></tr></thead><tbody><tr v-for="item in completed" :key="item.name" v-record="{ doctype: 'DTMGP Project Inspection', name: item.name }"><td><strong>{{ item.project }}</strong></td><td>{{ item.scheduled_date }}</td><td>{{ item.findings || '-' }}</td><td>{{ item.recommendation || '-' }}</td></tr></tbody></table><p v-if="!completed.length" class="users-empty">No completed inspection reports for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'gps-photo-evidence'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Coordinates</th><th>Photo evidence</th></tr></thead><tbody><tr v-for="item in geoTagged" :key="item.name" v-record="{ doctype: 'DTMGP Project Inspection', name: item.name }"><td><strong>{{ item.project }}</strong></td><td><a :href="mapLink(item.latitude as number, item.longitude as number)" target="_blank" rel="noopener">{{ item.latitude }}, {{ item.longitude }}</a></td><td><a v-if="item.photo_evidence" :href="item.photo_evidence" target="_blank" rel="noopener">View photo</a><span v-else>Not attached</span></td></tr></tbody></table><p v-if="!geoTagged.length" class="users-empty">No inspections with GPS coordinates recorded yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'inspection-exceptions'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Scheduled date</th><th>Exception reason</th></tr></thead><tbody><tr v-for="item in exceptions" :key="item.name" v-record="{ doctype: 'DTMGP Project Inspection', name: item.name }"><td><strong>{{ item.project }}</strong></td><td>{{ item.scheduled_date }}</td><td>{{ item.exception_reason || '-' }}</td></tr></tbody></table><p v-if="!exceptions.length" class="users-empty">No inspection exceptions recorded for this LGA.</p></div>
  </template>
</template>
