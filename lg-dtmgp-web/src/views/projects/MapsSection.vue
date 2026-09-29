<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import { mapLink } from "./types";
import type { MapsData } from "./types";

const props = defineProps<{ mapsData: MapsData }>();

const ITEM_LABELS: Record<string, string> = { "project-map": "Project Map", "asset-map": "Asset Map", "inspection-map": "Inspection Map" };
const DEFAULT_ITEM = "project-map";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
const activePoints = computed(() => activeItem.value === "asset-map" ? props.mapsData.assets : activeItem.value === "inspection-map" ? props.mapsData.inspections : props.mapsData.projects);
const mapUrl = computed(() => {
  const point = activePoints.value.find((item) => item.latitude && item.longitude);
  if (!point) return "";
  const lat = Number(point.latitude); const lon = Number(point.longitude); const pad = 0.03;
  return `https://www.openstreetmap.org/export/embed.html?bbox=${lon-pad}%2C${lat-pad}%2C${lon+pad}%2C${lat+pad}&layer=mapnik&marker=${lat}%2C${lon}`;
});
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <iframe v-if="mapUrl" :src="mapUrl" title="Scoped project and asset map" loading="lazy" style="border:1px solid var(--line);height:360px;margin-bottom:16px;width:100%"></iframe>

  <template v-if="activeItem === 'project-map'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Coordinates</th></tr></thead><tbody><tr v-for="item in mapsData.projects" :key="item.name"><td><strong>{{ item.project_name }}</strong></td><td><a :href="mapLink(item.latitude, item.longitude)" target="_blank" rel="noopener">{{ item.latitude }}, {{ item.longitude }}</a></td></tr></tbody></table><p v-if="!mapsData.projects.length" class="users-empty">No projects with a geo-tagged location yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'asset-map'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Asset</th><th>Coordinates</th></tr></thead><tbody><tr v-for="item in mapsData.assets" :key="item.name"><td><strong>{{ item.asset_name }}</strong></td><td><a :href="mapLink(item.latitude, item.longitude)" target="_blank" rel="noopener">{{ item.latitude }}, {{ item.longitude }}</a></td></tr></tbody></table><p v-if="!mapsData.assets.length" class="users-empty">No assets at a geo-tagged location yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'inspection-map'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Status</th><th>Coordinates</th></tr></thead><tbody><tr v-for="item in mapsData.inspections" :key="item.name"><td><strong>{{ item.project }}</strong></td><td>{{ item.status }}</td><td><a :href="mapLink(item.latitude, item.longitude)" target="_blank" rel="noopener">{{ item.latitude }}, {{ item.longitude }}</a></td></tr></tbody></table><p v-if="!mapsData.inspections.length" class="users-empty">No inspections with GPS evidence yet.</p></div>
  </template>
</template>
