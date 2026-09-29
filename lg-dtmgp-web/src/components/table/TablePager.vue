<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "@lucide/vue";

defineProps<{ page: number; pageSize: number; total: number; itemCount: number }>();
const emit = defineEmits<{ "change-page": [delta: number] }>();
</script>

<template>
  <footer class="table-footer">
    <span>Showing {{ itemCount }} of {{ total }}</span>
    <div>
      <button :disabled="page === 1" @click="emit('change-page', -1)"><ChevronLeft :size="14" /> Previous</button>
      <button class="current">{{ page }}</button>
      <button :disabled="page * pageSize >= total" @click="emit('change-page', 1)">Next <ChevronRight :size="14" /></button>
    </div>
  </footer>
</template>
