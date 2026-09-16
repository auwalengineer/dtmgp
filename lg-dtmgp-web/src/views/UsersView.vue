<script setup lang="ts">
import { Pencil, Plus, UserRoundCheck } from "@lucide/vue";
import { computed, ref, watch } from "vue";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface ManagedUser { name: string; full_name: string; enabled: number; lgas: string[]; roles: string[] }
const lgaRoles = ["LGA Administrator", "LGA Chairman", "LGA Secretary", "Treasurer", "HR Officer", "Procurement Officer", "Project Officer", "Traditional Affairs Officer", "Internal Auditor", "Read-only Officer"];
const stateRoles = ["State Administrator", "State Executive Viewer", "State Auditor"];
const session = useSessionStore();
const users = ref<ManagedUser[]>([]);
const loading = ref(true);
const busy = ref(false);
const showForm = ref(false);
const editingUser = ref<string | null>(null);
const error = ref("");
const form = ref(emptyForm());
const availableRoles = computed(() => session.canChangeLga ? [...stateRoles, ...lgaRoles] : lgaRoles);

function emptyForm() {
  return { email: "", first_name: "", last_name: "", role: "HR Officer", company: session.activeLga, temporary_password: "" };
}

async function loadUsers() {
  loading.value = true;
  error.value = "";
  try {
    const company = session.activeLga ? `?company=${encodeURIComponent(session.activeLga)}` : "";
    users.value = (await apiRequest<{ items: ManagedUser[] }>(`/api/method/dtmgp.api.v1.users.list_users${company}`)).items;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load users";
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editingUser.value = null;
  form.value = emptyForm();
  showForm.value = true;
}

function openEdit(user: ManagedUser) {
  const names = user.full_name.trim().split(/\s+/);
  editingUser.value = user.name;
  form.value = {
    email: user.name,
    first_name: names.shift() || user.full_name,
    last_name: names.join(" "),
    role: user.roles[0] || "HR Officer",
    company: user.lgas[0] || session.activeLga,
    temporary_password: "",
  };
  showForm.value = true;
}

async function saveUser() {
  busy.value = true;
  error.value = "";
  try {
    if (editingUser.value) {
      await apiRequest("/api/method/dtmgp.api.v1.users.update_user", {
        method: "POST",
        body: JSON.stringify({ user: editingUser.value, first_name: form.value.first_name, last_name: form.value.last_name, role: form.value.role, company: form.value.company }),
      });
    } else {
      await apiRequest("/api/method/dtmgp.api.v1.users.create_user", { method: "POST", body: JSON.stringify(form.value) });
    }
    showForm.value = false;
    await loadUsers();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to save user";
  } finally {
    busy.value = false;
  }
}

async function toggleUser(user: ManagedUser) {
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.users.set_user_enabled", { method: "POST", body: JSON.stringify({ user: user.name, enabled: user.enabled ? 0 : 1 }) });
    await loadUsers();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to update user";
  }
}

watch(() => session.activeLga, loadUsers, { immediate: true });
</script>

<template>
  <section class="page-heading">
    <div><p class="eyebrow">Administration</p><h1>User management</h1><p>{{ session.activeLga }}</p></div>
    <button class="primary-action" @click="openCreate"><Plus :size="17" /> Add user</button>
  </section>
  <section class="users-panel">
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <p v-if="loading" class="users-empty">Loading users...</p>
    <div v-else class="user-list">
      <article v-for="user in users" :key="user.name">
        <span class="user-list-avatar"><UserRoundCheck :size="20" /></span>
        <div><strong>{{ user.full_name }}</strong><small>{{ user.name }}</small></div>
        <span>{{ user.roles.join(", ") || "No platform role" }}</span>
        <span>{{ user.lgas.map(lga => lga.replace(" Local Government Area", " LGA")).join(", ") }}</span>
        <div class="user-row-actions">
          <button class="icon-button" title="Edit user" :disabled="user.name === session.user.email" @click="openEdit(user)"><Pencil :size="17" /></button>
          <button class="secondary-action" :disabled="user.name === session.user.email" @click="toggleUser(user)">{{ user.enabled ? "Disable" : "Enable" }}</button>
        </div>
      </article>
      <p v-if="!users.length" class="users-empty">No users found in this LGA.</p>
    </div>
  </section>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
    <form class="user-modal" @submit.prevent="saveUser">
      <h2>{{ editingUser ? "Edit staff user" : "Add staff user" }}</h2>
      <label>Email<input v-model="form.email" type="email" required :disabled="Boolean(editingUser)" /></label>
      <label>First name<input v-model="form.first_name" required /></label>
      <label>Last name<input v-model="form.last_name" /></label>
      <label>Role<select v-model="form.role"><option v-for="role in availableRoles" :key="role">{{ role }}</option></select></label>
      <label>LGA<select v-model="form.company" :disabled="!session.canChangeLga"><option v-for="lga in session.allowedLgas" :key="lga">{{ lga }}</option></select></label>
      <label v-if="!editingUser">Temporary password<input v-model="form.temporary_password" type="password" minlength="8" /></label>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="busy">{{ busy ? "Saving..." : "Save user" }}</button></footer>
    </form>
  </div>
</template>
