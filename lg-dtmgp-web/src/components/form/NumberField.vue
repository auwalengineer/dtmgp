<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; min?: number; max?: number; step?: number; disabled?: boolean; placeholder?: string }>();
const model = defineModel<number>({ default: 0 });
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth">
    <input type="number" v-model.number="model" :required="required" :disabled="disabled" :min="min" :max="max" :step="step" :placeholder="placeholder" :aria-invalid="!!error" />
  </BaseField>
</template>
