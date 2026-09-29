<script setup lang="ts">
defineProps<{ label: string; disabled?: boolean; fullWidth?: boolean }>();
const model = defineModel<0 | 1>({ default: 0 });

function onChange(event: Event) {
  model.value = (event.target as HTMLInputElement).checked ? 1 : 0;
}
</script>

<template>
  <label class="field field-checkbox" :class="{ 'full-field': fullWidth }">
    <input type="checkbox" :checked="model === 1" :disabled="disabled" @change="onChange" />
    <span>{{ label }}</span>
  </label>
</template>
