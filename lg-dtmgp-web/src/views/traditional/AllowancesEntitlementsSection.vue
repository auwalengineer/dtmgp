<script setup lang="ts">
import { History, ListChecks, Wallet } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "entitlement-register": "Entitlement Register", "allowance-processing": "Allowance Processing", "payment-history": "Payment History" };
const DEFAULT_ITEM = "entitlement-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'entitlement-register'">
    <PreviewCard :icon="ListChecks" title="Entitlement register" body="A register of statutory allowances and entitlements per ruler or institution isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'allowance-processing'">
    <PreviewCard :icon="Wallet" title="Allowance processing" body="Processing of allowance payments isn't available yet — like HR payroll, this would carry Restricted financial data pending sign-off once scoped." />
  </template>
  <template v-else-if="activeItem === 'payment-history'">
    <PreviewCard :icon="History" title="Payment history" body="A payment history for traditional allowances isn't available yet." />
  </template>
</template>
