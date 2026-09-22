<script setup lang="ts">
import { FilePlus2, ScrollText } from "@lucide/vue";
import { reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { Options, Project, Task } from "./types";

const props = defineProps<{ projects: Project[]; tasks: Task[]; milestones: Task[]; options: Options; canManage: boolean }>();
const emit = defineEmits<{ "new-task": [isMilestone: number]; "save-project": [name: string, values: Record<string, string>] }>();

const ITEM_LABELS: Record<string, string> = { "project-proposals": "Project Proposals", "work-plans": "Work Plans", "project-locations": "Project Locations", "project-milestones": "Project Milestones", "funding-sources": "Funding Sources" };
const DEFAULT_ITEM = "project-proposals";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const editedLocation = reactive<Record<string, string>>({});
const editedFunding = reactive<Record<string, string>>({});
watch(() => props.projects, (projects) => { for (const project of projects) { editedLocation[project.name] ??= project.dtmgp_location || ""; editedFunding[project.name] ??= project.dtmgp_funding_source || ""; } }, { immediate: true });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'project-proposals'">
    <PreviewCard :icon="ScrollText" title="Project proposals" body="A pre-approval proposal intake distinct from the project register isn't modeled yet -- ERPNext's Project doctype only tracks a project once it exists, not a proposal awaiting approval." />
  </template>

  <template v-else-if="activeItem === 'work-plans'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Work plans</h3><button v-if="canManage" class="secondary-action" @click="emit('new-task', 0)"><FilePlus2 :size="15" /> New task</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Task</th><th>Project</th><th>Status</th><th>Start</th><th>End</th><th>Progress</th></tr></thead><tbody><tr v-for="item in tasks" :key="item.name"><td><strong>{{ item.subject }}</strong></td><td>{{ item.project }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td>{{ item.exp_start_date || '-' }}</td><td>{{ item.exp_end_date || '-' }}</td><td>{{ item.progress }}%</td></tr></tbody></table><p v-if="!tasks.length" class="users-empty">No work plan tasks recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'project-locations'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Location</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in projects" :key="item.name"><td><strong>{{ item.project_name }}</strong></td><td><select v-if="canManage" v-model="editedLocation[item.name]"><option value="">No location set</option><option v-for="loc in options.locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option></select><span v-else>{{ item.dtmgp_location || '-' }}</span></td><td v-if="canManage"><button v-if="editedLocation[item.name] !== (item.dtmgp_location || '')" class="secondary-action compact-action" @click="emit('save-project', item.name, { dtmgp_location: editedLocation[item.name] })">Save</button></td></tr></tbody></table><p v-if="!projects.length" class="users-empty">No projects recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'project-milestones'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Project milestones</h3><button v-if="canManage" class="secondary-action" @click="emit('new-task', 1)"><FilePlus2 :size="15" /> New milestone</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Milestone</th><th>Project</th><th>Status</th><th>Target date</th></tr></thead><tbody><tr v-for="item in milestones" :key="item.name"><td><strong>{{ item.subject }}</strong></td><td>{{ item.project }}</td><td><span class="table-status" :class="item.status === 'Completed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.exp_end_date || '-' }}</td></tr></tbody></table><p v-if="!milestones.length" class="users-empty">No milestones recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'funding-sources'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Funding source</th><th v-if="canManage"></th></tr></thead><tbody><tr v-for="item in projects" :key="item.name"><td><strong>{{ item.project_name }}</strong></td><td><select v-if="canManage" v-model="editedFunding[item.name]"><option value="">No source set</option><option>State</option><option>Federal</option><option>Donor</option><option>LGA Counterpart</option><option>Other</option></select><span v-else>{{ item.dtmgp_funding_source || '-' }}</span></td><td v-if="canManage"><button v-if="editedFunding[item.name] !== (item.dtmgp_funding_source || '')" class="secondary-action compact-action" @click="emit('save-project', item.name, { dtmgp_funding_source: editedFunding[item.name] })">Save</button></td></tr></tbody></table><p v-if="!projects.length" class="users-empty">No projects recorded for this LGA.</p></div>
  </template>
</template>
