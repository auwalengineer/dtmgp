<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";

import AppSidebar from "@/components/AppSidebar.vue";
import AppTopbar from "@/components/AppTopbar.vue";

const navigationOpen = ref(false);
const route = useRoute();
const updateAvailable = ref(false);
let updateTimer: number | undefined;

async function checkVersion() {
  try {
    const response = await fetch("/version.json", { cache: "no-store" });
    if (!response.ok) return;
    const deployed = await response.json() as { commit?: string };
    updateAvailable.value = Boolean(deployed.commit && deployed.commit !== "development" && deployed.commit !== __BUILD_VERSION__);
  } catch { /* A version check must never interrupt application work. */ }
}
function refresh() { window.location.reload(); }
onMounted(() => { void checkVersion(); updateTimer = window.setInterval(checkVersion, 300_000); });
onUnmounted(() => window.clearInterval(updateTimer));
</script>

<template>
  <aside v-if="updateAvailable" class="version-banner" role="status"><span>A newer version is available.</span><button @click="refresh">Refresh</button></aside>
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
