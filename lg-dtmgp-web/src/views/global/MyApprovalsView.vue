<script setup lang="ts">
import { onMounted, ref } from "vue";

import { apiRequest } from "@/services/api";
import { openRecordDetails } from "@/services/recordDetails";

interface ApprovalItem { doctype: string; name: string; title: string; company: string; status: string }

const items = ref<ApprovalItem[]>([]);
const governanceScoped = ref(true);
const loading = ref(true);
const error = ref("");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const result = await apiRequest<{ items: ApprovalItem[]; governance_scoped: boolean }>("/api/method/dtmgp.api.v1.personal.get_my_approvals");
    items.value = result.items;
    governanceScoped.value = result.governance_scoped;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load your approvals"; }
  finally { loading.value = false; }
}
onMounted(load);
</script>

<template>
  <section class="page-heading"><div><p class="eyebrow">Personal Workspace</p><h1>My Approvals</h1><p>Records awaiting your decision</p></div></section>

  <p v-if="governanceScoped" class="users-empty" style="text-align:left;padding:0 0 16px">
    This currently shows Administration &amp; Governance's approvals inbox. Finance, HR and Traditional Affairs each still track their own pending approvals separately within their own workspace — a single cross-module inbox is planned but not built yet.
  </p>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading your approvals...</p>
  <div v-else class="staff-table-wrap">
    <table class="staff-table finance-table">
      <thead><tr><th>Reference</th><th>Type</th><th>Title</th><th>LGA</th><th>Status</th></tr></thead>
      <tbody>
        <tr v-for="item in items" :key="item.doctype + item.name" class="record-row" @click="openRecordDetails({ doctype: item.doctype, name: item.name })">
          <td><strong>{{ item.name }}</strong></td>
          <td>{{ item.doctype.replace("DTMGP ", "") }}</td>
          <td>{{ item.title }}</td>
          <td>{{ item.company }}</td>
          <td><span class="table-status neutral">{{ item.status }}</span></td>
        </tr>
      </tbody>
    </table>
    <p v-if="!items.length" class="users-empty">Nothing is awaiting your approval right now.</p>
  </div>
</template>
