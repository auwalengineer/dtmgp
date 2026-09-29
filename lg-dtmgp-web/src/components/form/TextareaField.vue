<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; disabled?: boolean; placeholder?: string }>();
const model = defineModel<string>({ default: "" });
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth ?? true">
    <textarea v-model="model" :required="required" :disabled="disabled" :placeholder="placeholder" :aria-invalid="!!error"></textarea>
  </BaseField>
</template>
