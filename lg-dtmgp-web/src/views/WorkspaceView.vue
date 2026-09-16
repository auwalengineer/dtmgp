<script setup lang="ts">
import { ClipboardList } from "@lucide/vue";
import { computed } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore, type NavigationItem } from "@/stores/session";

const route = useRoute();
const session = useSessionStore();
const destination = computed(() => {
  const domain = String(route.params.domain || "");
  const sectionId = String(route.params.section || "");
  const itemId = String(route.params.item || "");
  const module = session.navigation.find(entry => entry.id === domain);
  const section = module?.children.find(entry => entry.id === sectionId);
  const item = section?.children?.find((entry: NavigationItem) => entry.id === itemId);
  const global = session.globalMenu.find(entry => entry.to === route.path);
  return { module: module?.label || "Personal Workspace", section: section?.label || "", title: global?.label || item?.label || section?.label || "Workspace" };
});
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">{{ destination.module }}</p><h1>{{ destination.title }}</h1><p>{{ session.activeLga }}</p></div></section>
  <section class="module-empty"><ClipboardList :size="36" /><h2>{{ destination.title }}</h2><p>This authorized workspace is registered in the navigation contract. Its records and workflow will be connected in the corresponding domain milestone.</p><span v-if="destination.section" class="status-badge">{{ destination.section }}</span></section>
</template>
