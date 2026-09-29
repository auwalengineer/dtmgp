<script setup lang="ts">
defineProps<{ count?: number }>();
</script>

<template>
  <span v-if="count" class="pending-badge" :aria-label="`${count} pending`">{{ count > 99 ? "99+" : count }}</span>
  <span v-else class="notification-dot" />
</template>
