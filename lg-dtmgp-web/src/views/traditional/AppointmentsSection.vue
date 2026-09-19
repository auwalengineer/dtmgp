<script setup lang="ts">
import { CircleCheck, ClipboardList, FileCheck2, ListChecks, Stamp, UserPlus } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "appointment-applications": "Appointment Applications", "selection-processes": "Selection Processes", "appointment-reviews": "Appointment Reviews", "pending-recognition": "Pending Recognition", "approved-appointments": "Approved Appointments", "installation-records": "Installation Records" };
const DEFAULT_ITEM = "appointment-applications";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'appointment-applications'">
    <PreviewCard :icon="UserPlus" title="Appointment applications" body="Intake of applications for a traditional appointment isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'selection-processes'">
    <PreviewCard :icon="ListChecks" title="Selection processes" body="Tracking of an in-progress selection process (candidates, stages, dates) isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'appointment-reviews'">
    <PreviewCard :icon="ClipboardList" title="Appointment reviews" body="A review/vetting workflow for proposed appointments isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'pending-recognition'">
    <PreviewCard :icon="FileCheck2" title="Pending recognition" body="Appointments awaiting state recognition aren't tracked yet — this depends on the Recognition & Certification domain being built alongside Appointments." />
  </template>
  <template v-else-if="activeItem === 'approved-appointments'">
    <PreviewCard :icon="CircleCheck" title="Approved appointments" body="A register of approved traditional appointments isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'installation-records'">
    <PreviewCard :icon="Stamp" title="Installation records" body="Records of installation ceremonies (date, officiants, witnesses) aren't tracked yet." />
  </template>
</template>
