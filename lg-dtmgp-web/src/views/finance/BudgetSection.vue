<script setup lang="ts">
import { BarChart3, ClipboardList, FileCheck2, History, PenLine, ScrollText, TrendingUp } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "budget-preparation": "Budget Preparation", "budget-proposals": "Budget Proposals", "budget-review": "Budget Review", "approved-budget": "Approved Budget", "budget-revisions": "Budget Revisions", "budget-performance": "Budget Performance", "variance-analysis": "Variance Analysis" };
const DEFAULT_ITEM = "budget-preparation";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'budget-preparation'">
    <PreviewCard :icon="PenLine" title="Budget preparation" body="Annual budget preparation (line items against ERPNext Budget) isn't wired into the platform yet — no budget module exists in the finance API today." />
  </template>
  <template v-else-if="activeItem === 'budget-proposals'">
    <PreviewCard :icon="ScrollText" title="Budget proposals" body="Departmental budget proposal intake isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'budget-review'">
    <PreviewCard :icon="ClipboardList" title="Budget review" body="A budget review and comment workflow isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'approved-budget'">
    <PreviewCard :icon="FileCheck2" title="Approved budget" body="A read view of the approved budget by account and cost center isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'budget-revisions'">
    <PreviewCard :icon="History" title="Budget revisions" body="Tracking of in-year budget revisions isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'budget-performance'">
    <PreviewCard :icon="TrendingUp" title="Budget performance" body="Actual-versus-budget performance tracking isn't available yet — it depends on budget data being connected first." />
  </template>
  <template v-else-if="activeItem === 'variance-analysis'">
    <PreviewCard :icon="BarChart3" title="Variance analysis" body="Budget variance analysis by account isn't available yet." />
  </template>
</template>
