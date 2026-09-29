<script setup lang="ts">
import { ref, watch } from "vue";

import FormActions from "../form/FormActions.vue";
import TextareaField from "../form/TextareaField.vue";

const props = defineProps<{ open: boolean; title: string; label?: string; saving?: boolean; error?: string }>();
const emit = defineEmits<{ confirm: [reason: string]; cancel: [] }>();

const reason = ref("");
watch(() => props.open, (open) => { if (open) reason.value = ""; });

function submit() {
  if (!reason.value.trim()) return;
  emit("confirm", reason.value.trim());
}
</script>

<template>
  <div v-if="open" class="modal-backdrop" @click.self="$emit('cancel')">
    <form class="user-modal" @submit.prevent="submit">
      <h2>{{ title }}</h2>
      <TextareaField v-model="reason" :label="label || 'Reason'" required hint="This reason is recorded with the decision." />
      <FormActions :saving="saving" :error="error" save-label="Submit" :disabled="!reason.trim()" @cancel="$emit('cancel')" />
    </form>
  </div>
</template>
