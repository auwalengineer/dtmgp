<script setup lang="ts">
import type { Component } from "vue";

defineProps<{ icon: Component; title: string; body: string }>();
</script>

<template>
  <div class="hr-tab-preview"><component :is="icon" :size="34" /><h2>{{ title }}</h2><p>{{ body }}</p><button type="button" class="secondary-action" disabled>Planned - not yet available</button></div>
</template>
