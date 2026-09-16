<script setup lang="ts">
import { BarChart3, BriefcaseBusiness, ChevronDown, CircleDollarSign, Crown, FolderKanban, Landmark, Settings, UsersRound, X } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/stores/session";

defineProps<{ open: boolean }>();
defineEmits<{ close: [] }>();
const session = useSessionStore();
const route = useRoute();
const expandedModule = ref("");
const expandedSection = ref("");
const icons = { landmark: Landmark, users: UsersRound, "circle-dollar-sign": CircleDollarSign, "folder-kanban": FolderKanban, crown: Crown, "chart-no-axes-combined": BarChart3, settings: Settings } as const;

function toggleModule(id: string) {
  expandedModule.value = expandedModule.value === id ? "" : id;
  expandedSection.value = "";
}
function toggleSection(id: string) { expandedSection.value = expandedSection.value === id ? "" : id; }
watch(() => route.fullPath, () => {
  const active = session.navigation.find(module => route.path.includes(module.id) || module.children.some(section => section.to === route.path));
  if (active) expandedModule.value = active.id;
}, { immediate: true });
</script>

<template>
  <button v-if="open" class="sidebar-backdrop" aria-label="Close navigation" @click="$emit('close')" />
  <aside class="sidebar" :class="{ 'sidebar--open': open }">
    <header class="brand">
      <img src="/benue-govt-logo.jpeg" alt="Benue State Government emblem" />
      <div><strong>LG-DTMGP</strong><span>Benue State</span></div>
      <button class="icon-button sidebar-close" title="Close navigation" @click="$emit('close')"><X :size="20" /></button>
    </header>
    <nav class="nested-navigation" aria-label="Primary navigation">
      <p class="nav-label">Authorized workspaces</p>
      <section v-for="module in session.navigation" :key="module.id" class="nav-module">
        <button class="nav-module-button" :class="{ active: expandedModule === module.id }" @click="toggleModule(module.id)">
          <component :is="icons[module.icon as keyof typeof icons] || BriefcaseBusiness" :size="18" />
          <span>{{ module.label }}</span><ChevronDown :size="15" />
        </button>
        <div v-if="expandedModule === module.id" class="nav-sections">
          <template v-for="section in module.children" :key="section.id">
            <RouterLink v-if="section.to" :to="section.to" class="nav-section-link" @click="$emit('close')">{{ section.label }}</RouterLink>
            <template v-else>
              <button class="nav-section-button" :class="{ active: expandedSection === `${module.id}-${section.id}` }" @click="toggleSection(`${module.id}-${section.id}`)"><span>{{ section.label }}</span><ChevronDown :size="14" /></button>
              <div v-if="expandedSection === `${module.id}-${section.id}`" class="nav-items">
                <RouterLink v-for="item in section.children" :key="item.id" :to="item.to || '/'" @click="$emit('close')">{{ item.label }}</RouterLink>
              </div>
            </template>
          </template>
        </div>
      </section>
    </nav>
    <footer class="sidebar-footer"><BriefcaseBusiness :size="18" /><span>Public Service Workspace</span></footer>
  </aside>
</template>
