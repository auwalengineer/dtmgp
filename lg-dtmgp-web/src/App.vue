<script setup lang="ts">
import { ref } from "vue";

import AppSidebar from "@/components/AppSidebar.vue";
import AppTopbar from "@/components/AppTopbar.vue";

const navigationOpen = ref(false);
</script>

<template>
  <div class="app-shell">
    <AppSidebar :open="navigationOpen" @close="navigationOpen = false" />
    <div class="app-workspace">
      <AppTopbar @open-navigation="navigationOpen = true" />
      <main class="page-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>
