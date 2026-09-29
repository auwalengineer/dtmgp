<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; disabled?: boolean; datetime?: boolean; min?: string; max?: string }>();
const model = defineModel<string>({ default: "" });
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth">
    <input :type="datetime ? 'datetime-local' : 'date'" v-model="model" :required="required" :disabled="disabled" :min="min" :max="max" :aria-invalid="!!error" />
  </BaseField>
</template>
