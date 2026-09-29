<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiRequest } from "@/services/api";
import { openRecordDetails } from "@/services/recordDetails";

interface Task { name: string; description: string; reference_type: string | null; reference_name: string | null; date: string | null; priority: string }

const tasks = ref<Task[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try { tasks.value = (await apiRequest<{ items: Task[] }>("/api/method/dtmgp.api.v1.personal.get_my_tasks")).items; }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load your tasks"; }
  finally { loading.value = false; }
}
onMounted(load);

function open(task: Task) {
  if (task.reference_type && task.reference_name) openRecordDetails({ doctype: task.reference_type, name: task.reference_name });
}
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">Personal Workspace</p><h1>My Tasks</h1><p>Open ToDos assigned to you</p></div></section>

  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading your tasks...</p>
  <div v-else class="staff-table-wrap">
    <table class="staff-table finance-table">
      <thead><tr><th>Task</th><th>Related record</th><th>Priority</th><th>Due</th></tr></thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.name" :class="{ 'record-row': task.reference_type }" @click="open(task)">
          <td><strong>{{ task.description || task.name }}</strong></td>
          <td>{{ task.reference_type ? `${task.reference_type} ${task.reference_name}` : "-" }}</td>
          <td><span class="table-status neutral">{{ task.priority }}</span></td>
          <td>{{ task.date || "-" }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!tasks.length" class="users-empty">Nothing assigned to you right now.</p>
  </div>
</template>
