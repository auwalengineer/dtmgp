<script setup lang="ts">
import { ArrowRight, ClipboardList } from "@lucide/vue";
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const moduleName = computed(() => String(route.params.module || "").split("-").map((part) => part[0].toUpperCase() + part.slice(1)).join(" "));
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">Operational module</p><h1>{{ moduleName }}</h1><p>Benue State Local Government Administration</p></div></section>
  <section class="module-empty"><ClipboardList :size="36" /><h2>{{ moduleName }} workspace</h2><p>Module workflows will be connected after the foundation and permission contracts are approved.</p><button class="secondary-action">View planned workflows <ArrowRight :size="16" /></button></section>
</template>
