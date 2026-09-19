<script setup lang="ts">
defineProps<{ items: { id: string; label: string }[]; activeId: string }>();
defineEmits<{ select: [id: string] }>();
</script>

<template>
  <nav class="hr-tabs hr-item-tabs" aria-label="Section views"><button v-for="item in items" :key="item.id" :class="{ active: activeId === item.id }" @click="$emit('select', item.id)">{{ item.label }}</button></nav>
</template>
