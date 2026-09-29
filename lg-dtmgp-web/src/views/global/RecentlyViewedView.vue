<script setup lang="ts">
import { ref } from "vue";

import { openRecordDetails } from "@/services/recordDetails";
import { clearRecentlyViewed, getRecentlyViewed } from "@/services/recentlyViewed";

const items = ref(getRecentlyViewed());

function clear() {
  clearRecentlyViewed();
  items.value = [];
}
</script>

<template>
  <section class="page-heading">
    <div><p class="eyebrow">Personal Workspace</p><h1>Recently Viewed</h1><p>Records you've opened on this device</p></div>
    <button v-if="items.length" class="secondary-action" type="button" @click="clear">Clear</button>
  </section>

  <p class="users-empty" style="text-align:left;padding:0 0 16px">
    This list is remembered on this device/browser only — it is not shared between devices and nothing here is sent to or stored by the server.
  </p>

  <div class="staff-table-wrap">
    <table class="staff-table finance-table">
      <thead><tr><th>Record</th><th>Type</th><th>Viewed</th></tr></thead>
      <tbody>
        <tr v-for="item in items" :key="item.doctype + item.name" class="record-row" @click="openRecordDetails({ doctype: item.doctype, name: item.name })">
          <td><strong>{{ item.title }}</strong><br /><small>{{ item.name }}</small></td>
          <td>{{ item.doctype.replace("DTMGP ", "") }}</td>
          <td>{{ item.viewedAt }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!items.length" class="users-empty">No records opened yet — records you view across the app will appear here.</p>
  </div>
</template>
