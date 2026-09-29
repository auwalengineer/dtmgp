<script setup lang="ts">
import { useSessionStore } from "@/stores/session";

const session = useSessionStore();
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">Personal Workspace</p><h1>Help &amp; Support</h1><p>Getting access, and what to do when something looks wrong</p></div></section>

  <div class="staff-table-wrap">
    <table class="staff-table">
      <tbody>
        <tr><td style="width:220px">Requesting a role or LGA change</td><td>Contact your LGA's User Administrator (or a State Administrator, for a state-level role). Access is granted per LGA — a role in one LGA does not carry over to another.</td></tr>
        <tr><td>"You are not permitted to..." errors</td><td>This means your account's role or assigned LGA doesn't cover that record — it isn't a bug. If you believe it's wrong, ask your User Administrator to review your role/LGA assignment.</td></tr>
        <tr><td>A record looks wrong or missing</td><td>Check you're viewing the correct LGA (top-right LGA switcher, if you have access to more than one). If the record genuinely looks incorrect, report it through your organization's normal support channel with the record's ID.</td></tr>
        <tr><td>Password reset</td><td>Use "Forgot password" on the login page, or ask a User Administrator to reset it for you.</td></tr>
        <tr><td>Your account</td><td>Signed in as {{ session.user.email }} ({{ session.user.role }}{{ session.activeLga ? `, ${session.activeLga}` : "" }}) — see My Profile for details.</td></tr>
      </tbody>
    </table>
  </div>

  <p class="users-empty" style="text-align:left;padding:16px 0">
    A dedicated support ticketing/escalation channel is not yet configured for this platform — this page will be updated with those contact details once the hosting operator's support process is finalized.
  </p>
</template>
