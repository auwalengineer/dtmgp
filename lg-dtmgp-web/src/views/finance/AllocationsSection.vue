<script setup lang="ts">
import { Inbox, ListChecks, PieChart, Receipt } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "allocation-register": "Allocation Register", "allocation-receipts": "Allocation Receipts", "allocation-distribution": "Allocation Distribution", "allocation-utilization": "Allocation Utilization" };
const DEFAULT_ITEM = "allocation-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'allocation-register'">
    <PreviewCard :icon="ListChecks" title="Allocation register" body="A register of statutory allocations (federal/state transfers) received by the LGA isn't modeled yet — no allocation doctype exists in the finance API today." />
  </template>
  <template v-else-if="activeItem === 'allocation-receipts'">
    <PreviewCard :icon="Inbox" title="Allocation receipts" body="Recording of received allocation tranches isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'allocation-distribution'">
    <PreviewCard :icon="PieChart" title="Allocation distribution" body="How an allocation is distributed across departments or projects isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'allocation-utilization'">
    <PreviewCard :icon="Receipt" title="Allocation utilization" body="Tracking how much of an allocation has been utilized isn't available yet." />
  </template>
</template>
