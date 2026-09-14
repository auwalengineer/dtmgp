<script setup lang="ts">
import { ref } from "vue";
import { useRoute } from "vue-router";

import AppSidebar from "@/components/AppSidebar.vue";
import AppTopbar from "@/components/AppTopbar.vue";

const navigationOpen = ref(false);
const route = useRoute();
</script>

<template>
  <RouterView v-if="route.meta.public" />
  <div v-else class="app-shell">
    <AppSidebar :open="navigationOpen" @close="navigationOpen = false" />
    <div class="app-workspace">
      <AppTopbar @open-navigation="navigationOpen = true" />
      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
