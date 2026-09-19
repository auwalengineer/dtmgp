<script setup lang="ts">
import { FileStack, FileWarning, Gavel, Scale, ScrollText, ShieldQuestion, Undo2 } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "new-petitions": "New Petitions", "petition-register": "Petition Register", "dispute-cases": "Dispute Cases", hearings: "Hearings", "evidence-documents": "Evidence & Documents", "decisions-resolutions": "Decisions & Resolutions", appeals: "Appeals" };
const DEFAULT_ITEM = "new-petitions";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'new-petitions'">
    <PreviewCard :icon="FileWarning" title="New petitions" body="Filing a new petition or dispute over a traditional matter isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'petition-register'">
    <PreviewCard :icon="FileStack" title="Petition register" body="A register of all filed petitions isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'dispute-cases'">
    <PreviewCard :icon="ShieldQuestion" title="Dispute cases" body="Open dispute cases (parties, subject matter, status) aren't tracked yet." />
  </template>
  <template v-else-if="activeItem === 'hearings'">
    <PreviewCard :icon="Gavel" title="Hearings" body="Scheduling and records of dispute hearings aren't available yet." />
  </template>
  <template v-else-if="activeItem === 'evidence-documents'">
    <PreviewCard :icon="ScrollText" title="Evidence & documents" body="Evidence and supporting document attachment for a case isn't available yet — this class of record also awaits the same records/legal retention sign-off noted for HR personnel files." />
  </template>
  <template v-else-if="activeItem === 'decisions-resolutions'">
    <PreviewCard :icon="Scale" title="Decisions & resolutions" body="Recording the decision or resolution reached on a case isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'appeals'">
    <PreviewCard :icon="Undo2" title="Appeals" body="An appeals process against a decision isn't available yet." />
  </template>
</template>
