<script setup lang="ts">
defineProps<{ saving?: boolean; disabled?: boolean; saveLabel?: string; savingLabel?: string; cancelLabel?: string; error?: string }>();
defineEmits<{ cancel: [] }>();
</script>

<template>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <footer>
    <button type="button" class="secondary-action" @click="$emit('cancel')">{{ cancelLabel || "Cancel" }}</button>
    <button class="primary-action" :disabled="saving || disabled">{{ saving ? (savingLabel || "Saving...") : (saveLabel || "Save") }}</button>
  </footer>
</template>
