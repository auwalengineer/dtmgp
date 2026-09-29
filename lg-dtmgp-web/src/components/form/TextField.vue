<script setup lang="ts">
import BaseField from "./BaseField.vue";

defineProps<{ label: string; required?: boolean; error?: string; hint?: string; fullWidth?: boolean; type?: string; placeholder?: string; disabled?: boolean; maxlength?: number }>();
const model = defineModel<string>({ default: "" });
</script>

<template>
  <BaseField :label="label" :required="required" :error="error" :hint="hint" :full-width="fullWidth">
    <input :type="type || 'text'" v-model="model" :required="required" :disabled="disabled" :placeholder="placeholder" :maxlength="maxlength" :aria-invalid="!!error" />
  </BaseField>
</template>
