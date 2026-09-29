<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import { isNewProject, projectView } from "./types";
import type { Project } from "./types";

const props = defineProps<{ projects: Project[]; canManage: boolean }>();
defineEmits<{ "new-project": []; transition: [name: string, target: string] }>();

const ITEM_LABELS: Record<string, string> = { "project-register": "Project Register", "new-projects": "New Projects", "ongoing-projects": "Ongoing Projects", "completed-projects": "Completed Projects", "delayed-projects": "Delayed Projects", "suspended-projects": "Suspended Projects", "abandoned-projects": "Abandoned Projects" };
const DEFAULT_ITEM = "project-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const filtered = computed(() => {
  if (activeItem.value === "project-register") return props.projects;
  if (activeItem.value === "new-projects") return props.projects.filter(isNewProject);
  const view = activeItem.value.replace("-projects", "");
  return props.projects.filter((project) => projectView(project) === view);
});

const NEXT_ACTIONS: Record<string, { label: string; target: string }[]> = {
  Open: [{ label: "Put on hold", target: "On hold" }, { label: "Mark completed", target: "Completed" }, { label: "Cancel", target: "Cancelled" }],
  "On hold": [{ label: "Resume", target: "Open" }, { label: "Cancel", target: "Cancelled" }],
};
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <div class="directory-toolbar"><h3 style="margin:0;flex:1">{{ ITEM_LABELS[activeItem] }}</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-project')"><FilePlus2 :size="15" /> New project</button></div>
  <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Status</th><th>Progress</th><th>Expected end</th><th>Priority</th><th></th></tr></thead><tbody><tr v-for="item in filtered" :key="item.name" v-record="{ doctype: 'Project', name: item.name }"><td><strong>{{ item.project_name }}</strong><br /><small>{{ item.name }}</small></td><td><span class="table-status" :class="item.status === 'Completed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.percent_complete }}%</td><td>{{ item.expected_end_date || '-' }}</td><td>{{ item.priority }}</td><td><button v-for="action in (canManage ? NEXT_ACTIONS[item.status] || [] : [])" :key="action.target" class="secondary-action compact-action" style="margin:2px" @click="$emit('transition', item.name, action.target)">{{ action.label }}</button></td></tr></tbody></table><p v-if="!filtered.length" class="users-empty">No projects in this view for this LGA.</p></div>
</template>
