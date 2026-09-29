<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; accept?: string; disabled?: boolean }>();
const model = defineModel<File | null>({ default: null });

function onChange(event: Event) {
  model.value = (event.target as HTMLInputElement).files?.[0] || null;
}
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth">
    <input type="file" :accept="accept" :required="required && !model" :disabled="disabled" @change="onChange" />
    <span v-if="model" class="field-file-name">{{ model.name }}</span>
  </BaseField>
</template>
