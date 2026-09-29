<script setup lang="ts">
import { GitCommitHorizontal, Wallet } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { Project, Task } from "./types";

const props = defineProps<{ projects: Project[]; milestones: Task[] }>();

const ITEM_LABELS: Record<string, string> = { "physical-progress": "Physical Progress", "financial-progress": "Financial Progress", "milestone-status": "Milestone Status", "delayed-milestones": "Delayed Milestones", "variation-requests": "Variation Requests" };
const DEFAULT_ITEM = "physical-progress";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const delayedMilestones = computed(() => props.milestones.filter((m) => m.status === "Overdue"));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'physical-progress'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Project</th><th>Status</th><th>Physical progress</th></tr></thead><tbody><tr v-for="item in projects" :key="item.name" v-record="{ doctype: 'Project', name: item.name }"><td><strong>{{ item.project_name }}</strong></td><td><span class="table-status neutral">{{ item.status }}</span></td><td>{{ item.percent_complete }}%</td></tr></tbody></table><p v-if="!projects.length" class="users-empty">No projects recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'financial-progress'">
    <PreviewCard :icon="Wallet" title="Financial progress" body="Percentage financial drawdown against a project's budget isn't available yet -- it depends on a project being linked to Finance's budget and expenditure records, and Finance's own Budget module is itself still a placeholder." />
  </template>

  <template v-else-if="activeItem === 'milestone-status'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Milestone</th><th>Project</th><th>Status</th><th>Target date</th></tr></thead><tbody><tr v-for="item in milestones" :key="item.name" v-record="{ doctype: 'Task', name: item.name }"><td><strong>{{ item.subject }}</strong></td><td>{{ item.project }}</td><td><span class="table-status" :class="item.status === 'Completed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.exp_end_date || '-' }}</td></tr></tbody></table><p v-if="!milestones.length" class="users-empty">No milestones recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'delayed-milestones'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Milestone</th><th>Project</th><th>Target date</th></tr></thead><tbody><tr v-for="item in delayedMilestones" :key="item.name" v-record="{ doctype: 'Task', name: item.name }"><td><strong>{{ item.subject }}</strong></td><td>{{ item.project }}</td><td>{{ item.exp_end_date || '-' }}</td></tr></tbody></table><p v-if="!delayedMilestones.length" class="users-empty">No overdue milestones for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'variation-requests'">
    <PreviewCard :icon="GitCommitHorizontal" title="Variation requests" body="Recording and approving scope or cost variation requests against a project isn't available yet -- no change-order entity exists, the same gap Finance has for Contract Variations." />
  </template>
</template>
