<script setup lang="ts">
import { FilePlus2, Wrench } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { VehicleLogRecord, VehicleRecord } from "./types";

const props = defineProps<{ vehicles: VehicleRecord[]; vehicleLogs: VehicleLogRecord[]; canManage: boolean }>();
const emit = defineEmits<{ "new-vehicle": []; "new-log": [] }>();

const ITEM_LABELS: Record<string, string> = { "vehicle-register": "Vehicle Register", "vehicle-assignments": "Vehicle Assignments", "trip-records": "Trip Records", "fuel-records": "Fuel Records", "vehicle-maintenance": "Vehicle Maintenance", "insurance-licensing": "Insurance & Licensing", "driver-records": "Driver Records" };
const DEFAULT_ITEM = "vehicle-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const assigned = computed(() => props.vehicles.filter((v) => v.employee));
const fuelRecords = computed(() => props.vehicleLogs.filter((l) => l.fuel_qty > 0));
const insuranceDueSoon = (endDate: string | null) => !!endDate && endDate <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'vehicle-register'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Vehicle register</h3><button v-if="canManage" class="secondary-action" @click="emit('new-vehicle')"><FilePlus2 :size="15" /> New vehicle</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>License plate</th><th>Make / Model</th><th>Odometer</th><th>Driver</th></tr></thead><tbody><tr v-for="item in vehicles" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.make }} {{ item.model }}</td><td>{{ item.last_odometer.toLocaleString() }}</td><td>{{ item.employee || 'Unassigned' }}</td></tr></tbody></table><p v-if="!vehicles.length" class="users-empty">No vehicles registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'vehicle-assignments'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>License plate</th><th>Driver</th><th>Location</th></tr></thead><tbody><tr v-for="item in assigned" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.employee }}</td><td>{{ item.location || '-' }}</td></tr></tbody></table><p v-if="!assigned.length" class="users-empty">No vehicles currently assigned to a driver.</p></div>
  </template>

  <template v-else-if="activeItem === 'trip-records'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Trip records</h3><button v-if="canManage" class="secondary-action" @click="emit('new-log')"><FilePlus2 :size="15" /> New log entry</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Vehicle</th><th>Date</th><th>Odometer</th><th>Driver</th></tr></thead><tbody><tr v-for="item in vehicleLogs" :key="item.name"><td><strong>{{ item.license_plate }}</strong></td><td>{{ item.date }}</td><td>{{ item.odometer.toLocaleString() }}</td><td>{{ item.employee || '-' }}</td></tr></tbody></table><p v-if="!vehicleLogs.length" class="users-empty">No vehicle log entries recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'fuel-records'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Vehicle</th><th>Date</th><th>Fuel qty</th><th>Price</th><th>Supplier</th></tr></thead><tbody><tr v-for="item in fuelRecords" :key="item.name"><td><strong>{{ item.license_plate }}</strong></td><td>{{ item.date }}</td><td>{{ item.fuel_qty }}</td><td>{{ item.price.toLocaleString() }}</td><td>{{ item.supplier || '-' }}</td></tr></tbody></table><p v-if="!fuelRecords.length" class="users-empty">No fuel records recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'vehicle-maintenance'">
    <PreviewCard :icon="Wrench" title="Vehicle maintenance" body="A dedicated service/maintenance record per vehicle isn't wired into this workspace yet -- ERPNext's Vehicle Log has a Vehicle Service child table for this, but the create form here doesn't expose it yet." />
  </template>

  <template v-else-if="activeItem === 'insurance-licensing'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>License plate</th><th>Insurer</th><th>Policy no.</th><th>Expiry</th></tr></thead><tbody><tr v-for="item in vehicles" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.insurance_company || '-' }}</td><td>{{ item.policy_no || '-' }}</td><td><span class="table-status" :class="insuranceDueSoon(item.end_date) ? 'neutral' : 'success'">{{ item.end_date || 'Not recorded' }}</span></td></tr></tbody></table><p v-if="!vehicles.length" class="users-empty">No vehicles registered for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'driver-records'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Driver</th><th>Vehicle</th></tr></thead><tbody><tr v-for="item in assigned" :key="item.name"><td><strong>{{ item.employee }}</strong></td><td>{{ item.name }} — {{ item.make }} {{ item.model }}</td></tr></tbody></table><p v-if="!assigned.length" class="users-empty">No drivers currently assigned to a vehicle.</p></div>
  </template>
</template>
