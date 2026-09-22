<script setup lang="ts">
import { ArrowRight } from "@lucide/vue";
import { ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { LgaAccessRow, PlatformRole, RoleProfile, UserSession } from "./types";

const ITEM_LABELS: Record<string, string> = { roles: "Roles", "role-profiles": "Role Profiles", "lga-access": "LGA Access", "user-sessions": "User Sessions" };
const DEFAULT_ITEM = "roles";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const session = useSessionStore();
const roles = ref<PlatformRole[]>([]);
const profiles = ref<RoleProfile[]>([]);
const access = ref<LgaAccessRow[]>([]);
const sessions = ref<UserSession[]>([]);
const loading = ref(true);
const error = ref("");

function scopeQuery() { return session.activeLga ? `?company=${encodeURIComponent(session.activeLga)}` : ""; }

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [roles.value, profiles.value, access.value, sessions.value] = await Promise.all([
      apiRequest<PlatformRole[]>("/api/method/dtmgp.api.v1.administration.list_platform_roles"),
      apiRequest<RoleProfile[]>("/api/method/dtmgp.api.v1.administration.list_role_profiles"),
      apiRequest<LgaAccessRow[]>(`/api/method/dtmgp.api.v1.administration.list_lga_access${scopeQuery()}`),
      apiRequest<UserSession[]>(`/api/method/dtmgp.api.v1.administration.list_user_sessions${scopeQuery()}`),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load User Management"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, load, { immediate: true });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>
  <template v-else>
    <template v-if="activeItem === 'roles'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Platform roles</h3><RouterLink class="text-action" to="/administration/users">Manage users <ArrowRight :size="15" /></RouterLink></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Role</th><th>Desk access</th><th>Users in scope</th></tr></thead><tbody><tr v-for="item in roles" :key="item.role"><td><strong>{{ item.role }}</strong></td><td>{{ item.desk_access ? "Yes" : "No" }}</td><td>{{ item.user_count }}</td></tr></tbody></table></div>
    </template>

    <template v-else-if="activeItem === 'role-profiles'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Role profiles</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Profile</th><th>Roles</th></tr></thead><tbody><tr v-for="item in profiles" :key="item.name"><td><strong>{{ item.name }}</strong></td><td>{{ item.roles.join(", ") }}</td></tr></tbody></table><p v-if="!profiles.length" class="users-empty">No role profiles seeded yet.</p></div>
    </template>

    <template v-else-if="activeItem === 'lga-access'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">LGA access register</h3><RouterLink class="text-action" to="/administration/users">Edit access <ArrowRight :size="15" /></RouterLink></div>
      <div class="panel" v-for="row in access" :key="row.company" style="margin-bottom:16px">
        <header class="panel-header"><div><h2>{{ row.company.replace(" Local Government Area", " LGA") }}</h2><p>{{ row.users.length }} user(s) with access</p></div></header>
        <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>User</th><th>Role</th><th>Status</th></tr></thead><tbody><tr v-for="user in row.users" :key="user.name"><td><strong>{{ user.full_name }}</strong><br /><small>{{ user.name }}</small></td><td>{{ user.roles.join(", ") || "No platform role" }}</td><td><span class="table-status" :class="user.enabled ? 'success' : 'neutral'">{{ user.enabled ? "Active" : "Disabled" }}</span></td></tr></tbody></table></div>
      </div>
      <p v-if="!access.length" class="users-empty">No LGA access grants in scope.</p>
    </template>

    <template v-else-if="activeItem === 'user-sessions'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Active sessions</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>User</th><th>Session</th><th>IP address</th><th>Last activity</th><th>Status</th></tr></thead><tbody><tr v-for="row in sessions" :key="row.sid || row.lastupdate"><td>{{ row.user }}</td><td>{{ row.sid || "—" }}</td><td>{{ row.ipaddress || "—" }}</td><td>{{ row.lastupdate }}</td><td><span class="table-status" :class="row.status === 'Active' ? 'success' : 'neutral'">{{ row.status }}</span></td></tr></tbody></table><p v-if="!sessions.length" class="users-empty">No active sessions in scope.</p></div>
    </template>
  </template>
</template>
