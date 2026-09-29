<script setup lang="ts">
defineProps<{ open: boolean; title: string; message: string; confirmLabel?: string; cancelLabel?: string; danger?: boolean; saving?: boolean }>();
defineEmits<{ confirm: []; cancel: [] }>();
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="$emit('cancel')">
    <div class="user-modal" role="alertdialog" aria-modal="true">
      <h2>{{ title }}</h2>
      <p class="modal-copy">{{ message }}</p>
      <footer>
        <button type="button" class="secondary-action" @click="$emit('cancel')">{{ cancelLabel || "Cancel" }}</button>
        <button type="button" :class="danger ? 'secondary-action' : 'primary-action'" :style="danger ? 'border-color:var(--red);color:var(--red)' : ''" :disabled="saving" @click="$emit('confirm')">
          {{ saving ? "Working..." : (confirmLabel || "Confirm") }}
        </button>
      </footer>
    </div>
  </div>
</template>
