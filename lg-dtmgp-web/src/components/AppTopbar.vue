<script setup lang="ts">
import { Bell, ChevronDown, LockKeyhole, LogOut, Menu, Search } from "@lucide/vue";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useSessionStore } from "@/stores/session";

defineEmits<{ openNavigation: [] }>();
const session = useSessionStore();
const router = useRouter();
const userMenuOpen = ref(false);
async function logout() { userMenuOpen.value = false; await session.logout(); await router.push("/login"); }
</script>

<template>
  <header class="topbar">
    <button class="icon-button mobile-menu" title="Open navigation" @click="$emit('openNavigation')"><Menu :size="22" /></button>
    <label class="search-box"><Search :size="18" /><input type="search" placeholder="Search records" aria-label="Search records" /></label>
    <div class="topbar-actions">
      <label v-if="session.canChangeLga" class="lga-context">
        <span>Active LGA</span><select :value="session.activeLga" @change="session.setActiveLga(($event.target as HTMLSelectElement).value)"><option v-for="lga in session.allowedLgas" :key="lga" :value="lga">{{ lga }}</option></select><ChevronDown :size="16" />
      </label>
      <div v-else class="lga-context lga-context--locked" title="Your LGA is assigned by your administrator"><span>Active LGA</span><strong>{{ session.activeLga.replace(" Local Government Area", " LGA") }}</strong><LockKeyhole :size="15" /></div>
      <RouterLink class="icon-button notification-button" to="/workspace/global/notifications" title="Notifications"><Bell :size="20" /><span class="notification-dot" /></RouterLink>
      <div class="user-menu-wrap">
        <button class="user-menu" title="Open user menu" @click="userMenuOpen = !userMenuOpen"><span class="avatar">{{ session.userInitials }}</span><span class="user-copy"><strong>{{ session.user.name }}</strong><small>{{ session.user.role }}</small></span><ChevronDown :size="16" /></button>
        <div v-if="userMenuOpen" class="global-user-menu">
          <RouterLink v-for="item in session.globalMenu" :key="item.id" :to="item.to || '/'" @click="userMenuOpen = false">{{ item.label }}</RouterLink>
          <button @click="logout"><LogOut :size="16" />Sign out</button>
        </div>
      </div>
    </div>
  </header>
</template>
