<script setup lang="ts">
import { ChartColumn, Crown, Gavel, GitBranch, Landmark } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "traditional-institution-report": "Traditional Institution Report", "traditional-ruler-report": "Traditional Ruler Report", "appointment-report": "Appointment Report", "succession-report": "Succession Report", "petition-dispute-report": "Petition & Dispute Report" };
const DEFAULT_ITEM = "traditional-institution-report";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'traditional-institution-report'">
    <PreviewCard :icon="Landmark" title="Traditional institution report" body="A statewide summary of registered traditional institutions isn't available yet — it depends on the Traditional Institutions domain being built first." />
  </template>
  <template v-else-if="activeItem === 'traditional-ruler-report'">
    <PreviewCard :icon="Crown" title="Traditional ruler report" body="A statewide summary of traditional rulers (current, vacant stools, demographics) isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'appointment-report'">
    <PreviewCard :icon="ChartColumn" title="Appointment report" body="A summary of appointment activity and turnaround times isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'succession-report'">
    <PreviewCard :icon="GitBranch" title="Succession report" body="A summary of succession cases and outcomes isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'petition-dispute-report'">
    <PreviewCard :icon="Gavel" title="Petition & dispute report" body="A summary of petition and dispute case volumes and resolution times isn't available yet." />
  </template>
</template>
