<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; disabled?: boolean; options: { value: string; label: string }[]; placeholder?: string }>();
const model = defineModel<string>({ default: "" });
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth">
    <select v-model="model" :required="required" :disabled="disabled" :aria-invalid="!!error">
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
  </BaseField>
</template>
