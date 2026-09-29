<script setup lang="ts">
import { useSessionStore } from "@/stores/session";

const session = useSessionStore();
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">Personal Workspace</p><h1>My Profile</h1><p>Your account as this platform sees it</p></div></section>

  <div class="staff-table-wrap">
    <table class="staff-table">
      <tbody>
        <tr><td>Name</td><td>{{ session.user.name }}</td></tr>
        <tr><td>Email</td><td>{{ session.user.email }}</td></tr>
        <tr><td>Primary role</td><td>{{ session.user.role }}</td></tr>
        <tr><td>Assigned LGA</td><td>{{ session.activeLga || "Not assigned" }}</td></tr>
        <tr v-if="session.allowedLgas.length > 1"><td>All authorized LGAs</td><td>{{ session.allowedLgas.join(", ") }}</td></tr>
      </tbody>
    </table>
  </div>

  <p class="users-empty" style="text-align:left;padding:16px 0">
    To change your password or personal details, use Frappe's own account settings at
    <a class="text-action" href="/app/user-profile" target="_blank" rel="noopener">/app/user-profile</a>.
    Role and LGA assignment changes are made by a User Administrator under System Administration.
  </p>
</template>
