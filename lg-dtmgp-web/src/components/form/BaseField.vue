<script setup lang="ts">
defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean }>();
</script>

<template>
  <label class="field" :class="{ 'full-field': fullWidth }">
    <span>{{ label }}<span v-if="required" class="field-required" aria-hidden="true">*</span></span>
    <slot />
    <span v-if="error" class="field-error" role="alert">{{ error }}</span>
    <span v-else-if="hint" class="field-hint">{{ hint }}</span>
  </label>
</template>
