<script setup lang="ts">
import { ref, watch } from "vue";

import { apiRequest } from "@/services/api";

interface TimelineEvent { name: string; occurred_at: string; event_type: string; outcome: string; actor: string; summary: string }

const props = defineProps<{ doctype: string; name: string }>();

const events = ref<TimelineEvent[]>([]);
const loading = ref(true);
const error = ref("");

async function load() {
  if (!props.doctype || !props.name) return;
  loading.value = true;
  error.value = "";
  try {
    const result = await apiRequest<{ items: TimelineEvent[] }>(`/api/method/dtmgp.api.v1.records.get_record_timeline?doctype=${encodeURIComponent(props.doctype)}&name=${encodeURIComponent(props.name)}`);
    events.value = result.items;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load history";
  } finally {
    loading.value = false;
  }
}
watch(() => [props.doctype, props.name], load, { immediate: true });
</script>

<template>
  <p v-if="loading" class="users-empty">Loading history...</p>
  <p v-else-if="error" class="login-error" role="alert">{{ error }}</p>
  <template v-else>
    <ol class="record-timeline">
      <li v-for="event in events" :key="event.name" class="record-timeline-item">
        <span class="table-status" :class="event.outcome === 'Success' ? 'success' : 'neutral'">{{ event.outcome }}</span>
        <div>
          <strong>{{ event.summary }}</strong>
          <small>{{ event.actor }} · {{ event.occurred_at }}</small>
        </div>
      </li>
    </ol>
    <p v-if="!events.length" class="users-empty">No recorded history for this record yet.</p>
  </template>
</template>
