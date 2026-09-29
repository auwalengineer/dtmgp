<script setup lang="ts">
import { ref } from "vue";

import ConfirmDialog from "./ConfirmDialog.vue";
import RejectionReasonDialog from "./RejectionReasonDialog.vue";

export interface TransitionOption {
  label: string;
  target: string;
  /** Ask for a written reason before firing this transition (e.g. Reject/Return). */
  requiresReason?: boolean;
  /** Ask for a plain yes/no confirmation before firing this transition, with this message. */
  confirm?: string;
  /** Style the option as a destructive/negative action. */
  danger?: boolean;
}

defineProps<{ options: TransitionOption[]; disabled?: boolean; saving?: boolean }>();
const emit = defineEmits<{ transition: [target: string, reason?: string] }>();

const pendingConfirm = ref<TransitionOption | null>(null);
const pendingReason = ref<TransitionOption | null>(null);

function choose(option: TransitionOption) {
  if (option.requiresReason) { pendingReason.value = option; return; }
  if (option.confirm) { pendingConfirm.value = option; return; }
  emit("transition", option.target);
}
function confirmPlain() {
  if (!pendingConfirm.value) return;
  emit("transition", pendingConfirm.value.target);
  pendingConfirm.value = null;
}
function confirmWithReason(reason: string) {
  if (!pendingReason.value) return;
  emit("transition", pendingReason.value.target, reason);
  pendingReason.value = null;
}
</script>

<template>
  <span class="approval-panel">
    <button
      v-for="option in options"
      :key="option.target"
      type="button"
      class="secondary-action compact-action"
      :style="option.danger ? 'border-color:var(--red);color:var(--red)' : ''"
      :disabled="disabled"
      @click="choose(option)"
    >{{ option.label }}</button>
  </span>

  <ConfirmDialog
    :open="!!pendingConfirm"
    :title="pendingConfirm?.label || ''"
    :message="pendingConfirm?.confirm || ''"
    :danger="pendingConfirm?.danger"
    :saving="saving"
    @confirm="confirmPlain"
    @cancel="pendingConfirm = null"
  />
  <RejectionReasonDialog
    :open="!!pendingReason"
    :title="pendingReason?.label || ''"
    :saving="saving"
    @confirm="confirmWithReason"
    @cancel="pendingReason = null"
  />
</template>
