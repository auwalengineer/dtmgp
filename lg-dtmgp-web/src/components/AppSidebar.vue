<script setup lang="ts">
import {
  BarChart3,
  BriefcaseBusiness,
  Building2,
  CircleDollarSign,
  FolderKanban,
  Landmark,
  LayoutDashboard,
  UsersRound,
  X,
} from "@lucide/vue";

defineProps<{ open: boolean }>();
defineEmits<{ close: [] }>();

const navigation = [
  { label: "Overview", to: "/", icon: LayoutDashboard },
  { label: "Administration", to: "/administration", icon: Building2 },
  { label: "People & HR", to: "/people", icon: UsersRound },
  { label: "Finance & Revenue", to: "/finance", icon: CircleDollarSign },
  { label: "Projects & Assets", to: "/projects", icon: FolderKanban },
  { label: "Traditional Affairs", to: "/traditional-affairs", icon: Landmark },
  { label: "Analytics", to: "/analytics", icon: BarChart3 },
];
</script>

<template>
  <button v-if="open" class="sidebar-backdrop" aria-label="Close navigation" @click="$emit('close')" />
  <aside class="sidebar" :class="{ 'sidebar--open': open }">
    <header class="brand">
      <img src="/benue-govt-logo.jpeg" alt="Benue State Government emblem" />
      <div><strong>LG-DTMGP</strong><span>Benue State</span></div>
      <button class="icon-button sidebar-close" title="Close navigation" @click="$emit('close')"><X :size="20" /></button>
    </header>
    <nav aria-label="Primary navigation">
      <p class="nav-label">Operations</p>
      <RouterLink v-for="item in navigation" :key="item.to" :to="item.to" class="nav-item" @click="$emit('close')">
        <component :is="item.icon" :size="19" />
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
    <footer class="sidebar-footer"><BriefcaseBusiness :size="18" /><span>Public Service Workspace</span></footer>
  </aside>
</template>
