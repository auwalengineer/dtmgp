<script setup lang="ts">
import { Bell, ChevronDown, Menu, Search } from "@lucide/vue";

import { useSessionStore } from "@/stores/session";

defineEmits<{ openNavigation: [] }>();
const session = useSessionStore();
</script>

<template>
  <header class="topbar">
    <button class="icon-button mobile-menu" title="Open navigation" @click="$emit('openNavigation')"><Menu :size="22" /></button>
    <label class="search-box">
      <Search :size="18" />
      <input type="search" placeholder="Search records" aria-label="Search records" />
    </label>
    <div class="topbar-actions">
      <button class="lga-context"><span>Active LGA</span><strong>{{ session.activeLga }}</strong><ChevronDown :size="16" /></button>
      <button class="icon-button notification-button" title="Notifications"><Bell :size="20" /><span class="notification-dot" /></button>
      <button class="user-menu"><span class="avatar">AO</span><span class="user-copy"><strong>{{ session.user.name }}</strong><small>{{ session.user.role }}</small></span><ChevronDown :size="16" /></button>
    </div>
  </header>
</template>
