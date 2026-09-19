<script setup lang="ts">
import { Crown, IdCard, UserRoundX, Users } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "rulers-register": "Rulers Register", "current-rulers": "Current Rulers", "former-rulers": "Former Rulers", "vacant-stools": "Vacant Stools", "ruler-profiles": "Ruler Profiles" };
const DEFAULT_ITEM = "rulers-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'rulers-register'">
    <PreviewCard :icon="Crown" title="Rulers register" body="A statewide register of traditional rulers linked to their institution and stool isn't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'current-rulers'">
    <PreviewCard :icon="Users" title="Current rulers" body="A live list of currently reigning rulers per LGA isn't available yet — it depends on the rulers register being built first." />
  </template>
  <template v-else-if="activeItem === 'former-rulers'">
    <PreviewCard :icon="UserRoundX" title="Former rulers" body="A historical list of former rulers (reign dates, succession reason) isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'vacant-stools'">
    <PreviewCard :icon="Crown" title="Vacant stools" body="Tracking of currently vacant traditional stools awaiting succession isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'ruler-profiles'">
    <PreviewCard :icon="IdCard" title="Ruler profiles" body="Detailed per-ruler profile pages (biography, coronation date, honours) aren't available yet." />
  </template>
</template>
