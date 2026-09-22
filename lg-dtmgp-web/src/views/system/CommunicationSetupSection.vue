<script setup lang="ts">
import { BellOff } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { notifications: "Notifications", "email-templates": "Email Templates", "sms-templates": "SMS Templates", "notification-preferences": "Notification Preferences" };
const DEFAULT_ITEM = "notifications";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <PreviewCard :icon="BellOff" :title="ITEM_LABELS[activeItem]" body="Deduplicated reminders and escalations, plus the email/SMS delivery pipeline they'd run on, are listed as pending platform work (see docs/implementation-status.md's Notifications backlog item). Template management is deferred until that pipeline exists, so it isn't faked here." />
</template>
