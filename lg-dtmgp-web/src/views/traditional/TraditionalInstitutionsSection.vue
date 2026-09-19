<script setup lang="ts">
import { BookOpen, Building2, History, Landmark, MapPinned } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "institution-register": "Institution Register", "traditional-councils": "Traditional Councils", "districts-chiefdoms": "Districts & Chiefdoms", "institutional-profiles": "Institutional Profiles", "historical-records": "Historical Records" };
const DEFAULT_ITEM = "institution-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'institution-register'">
    <PreviewCard :icon="Building2" title="Institution register" body="A register of recognized traditional institutions per LGA (name, type, seat, founding basis) isn't modeled yet — no DocType or API exists for this domain." />
  </template>
  <template v-else-if="activeItem === 'traditional-councils'">
    <PreviewCard :icon="Landmark" title="Traditional councils" body="Traditional council composition and membership records aren't tracked yet — this whole domain is pending scope and data-model approval." />
  </template>
  <template v-else-if="activeItem === 'districts-chiefdoms'">
    <PreviewCard :icon="MapPinned" title="Districts & chiefdoms" body="A hierarchy of districts and chiefdoms under each institution isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'institutional-profiles'">
    <PreviewCard :icon="BookOpen" title="Institutional profiles" body="Detailed per-institution profile pages (jurisdiction, protocols, contacts) aren't available yet." />
  </template>
  <template v-else-if="activeItem === 'historical-records'">
    <PreviewCard :icon="History" title="Historical records" body="Archival and historical documentation for traditional institutions isn't available yet — see the Records & Legal sign-off condition in the implementation status doc for why this class of record is deferred." />
  </template>
</template>
