<script setup lang="ts">
import { Bell, ChevronDown, LockKeyhole, Menu, Search } from "@lucide/vue";

import { useSessionStore } from "@/stores/session";
import { useRouter } from "vue-router";

defineEmits<{ openNavigation: [] }>();
const session = useSessionStore();
const router = useRouter();
async function logout() { await session.logout(); await router.push("/login"); }
</script>

<template>
  <header class="topbar">
    <button class="icon-button mobile-menu" title="Open navigation" @click="$emit('openNavigation')"><Menu :size="22" /></button>
    <label class="search-box">
      <Search :size="18" />
      <input type="search" placeholder="Search records" aria-label="Search records" />
    </label>
    <div class="topbar-actions">
      <label v-if="session.canChangeLga" class="lga-context">
        <span>Active LGA</span>
        <select :value="session.activeLga" @change="session.setActiveLga(($event.target as HTMLSelectElement).value)">
          <option v-for="lga in session.allowedLgas" :key="lga" :value="lga">{{ lga }}</option>
        </select>
        <ChevronDown :size="16" />
      </label>
      <div v-else class="lga-context lga-context--locked" title="Your LGA is assigned by your administrator">
        <span>Active LGA</span><strong>{{ session.activeLga.replace(" Local Government Area", " LGA") }}</strong><LockKeyhole :size="15" />
      </div>
      <button class="icon-button notification-button" title="Notifications"><Bell :size="20" /><span class="notification-dot" /></button>
      <button class="user-menu" title="Sign out" @click="logout"><span class="avatar">{{ session.userInitials }}</span><span class="user-copy"><strong>{{ session.user.name }}</strong><small>{{ session.user.role }} · Sign out</small></span><ChevronDown :size="16" /></button>
    </div>
  </header>
</template>
