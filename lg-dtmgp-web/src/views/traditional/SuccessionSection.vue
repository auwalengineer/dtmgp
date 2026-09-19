<script setup lang="ts">
import { GitBranch, History, ListChecks, Users, Workflow } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "succession-cases": "Succession Cases", "ruling-houses": "Ruling Houses", "eligible-candidates": "Eligible Candidates", "selection-records": "Selection Records", "succession-history": "Succession History" };
const DEFAULT_ITEM = "succession-cases";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'succession-cases'">
    <PreviewCard :icon="GitBranch" title="Succession cases" body="Open succession cases following a vacant stool aren't tracked yet." />
  </template>
  <template v-else-if="activeItem === 'ruling-houses'">
    <PreviewCard :icon="Users" title="Ruling houses" body="A register of ruling houses eligible to present candidates for a stool isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'eligible-candidates'">
    <PreviewCard :icon="ListChecks" title="Eligible candidates" body="Candidate eligibility screening for succession isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'selection-records'">
    <PreviewCard :icon="Workflow" title="Selection records" body="Records of how a successor was selected (kingmakers, votes, consensus) aren't tracked yet." />
  </template>
  <template v-else-if="activeItem === 'succession-history'">
    <PreviewCard :icon="History" title="Succession history" body="A historical log of past successions per stool isn't available yet." />
  </template>
</template>
