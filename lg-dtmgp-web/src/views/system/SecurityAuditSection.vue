<script setup lang="ts">
import { ChevronLeft, ChevronRight } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";

import ItemTabs from "../shared/ItemTabs.vue";
import type { AuditEvent, LoginHistoryRow } from "./types";

const ITEM_LABELS: Record<string, string> = { "audit-logs": "Audit Logs", "login-history": "Login History", "permission-changes": "Permission Changes", "security-events": "Security Events", "data-export-history": "Data Export History" };
const DEFAULT_ITEM = "audit-logs";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const PAGE_SIZE = 20;
const auditItems = ref<AuditEvent[]>([]);
const loginItems = ref<LoginHistoryRow[]>([]);
const total = ref(0);
const page = ref(1);
const loading = ref(true);
const error = ref("");
const isLoginHistory = computed(() => activeItem.value === "login-history");

async function load() {
  loading.value = true;
  error.value = "";
  try {
    if (isLoginHistory.value) {
      const result = await apiRequest<{ items: LoginHistoryRow[]; total: number }>(`/api/method/dtmgp.api.v1.administration.list_login_history?page=${page.value}&page_size=${PAGE_SIZE}`);
      loginItems.value = result.items;
      total.value = result.total;
    } else {
      const params = new URLSearchParams({ page: String(page.value), page_size: String(PAGE_SIZE) });
      if (activeItem.value === "permission-changes") params.set("event_type", "permission_change,user_access_change");
      if (activeItem.value === "security-events") params.set("outcome", "Denied");
      if (activeItem.value === "data-export-history") params.set("event_type", "data_export");
      const result = await apiRequest<{ items: AuditEvent[]; total: number }>(`/api/method/dtmgp.api.v1.administration.list_audit_events?${params.toString()}`);
      auditItems.value = result.items;
      total.value = result.total;
    }
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load audit data"; }
  finally { loading.value = false; }
}
watch(activeItem, () => { page.value = 1; load(); }, { immediate: true });
function changePage(delta: number) { page.value += delta; load(); }
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <p v-if="activeItem === 'data-export-history'" class="users-empty" style="text-align:left;padding:0 20px">Exports are recorded when generated — from Analytics' "Export executive summary" action, which requires a stated purpose and marks the file's classification. This lists those audit events.</p>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>
  <template v-else-if="isLoginHistory">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>User</th><th>Operation</th><th>Status</th><th>When</th><th>IP address</th></tr></thead><tbody><tr v-for="item in loginItems" :key="item.name"><td><strong>{{ item.full_name }}</strong><br /><small>{{ item.user }}</small></td><td>{{ item.operation }}</td><td><span class="table-status" :class="item.status === 'Success' ? 'success' : 'neutral'">{{ item.status }}</span></td><td>{{ item.creation }}</td><td>{{ item.ip_address || "—" }}</td></tr></tbody></table>
      <footer class="table-footer"><span>Showing {{ loginItems.length }} of {{ total }}</span><div><button :disabled="page === 1" @click="changePage(-1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * PAGE_SIZE >= total" @click="changePage(1)">Next <ChevronRight :size="14" /></button></div></footer>
    </div>
    <p v-if="!loginItems.length" class="users-empty">No login activity recorded yet.</p>
  </template>
  <template v-else>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Event</th><th>Outcome</th><th>Actor</th><th>LGA</th><th>Summary</th><th>When</th></tr></thead><tbody><tr v-for="item in auditItems" :key="item.name"><td>{{ item.event_type }}</td><td><span class="table-status" :class="item.outcome === 'Success' ? 'success' : 'neutral'">{{ item.outcome }}</span></td><td>{{ item.actor }}</td><td>{{ item.company ? item.company.replace(" Local Government Area", " LGA") : "—" }}</td><td>{{ item.summary }}</td><td>{{ item.occurred_at }}</td></tr></tbody></table>
      <footer class="table-footer"><span>Showing {{ auditItems.length }} of {{ total }}</span><div><button :disabled="page === 1" @click="changePage(-1)"><ChevronLeft :size="14" /> Previous</button><button class="current">{{ page }}</button><button :disabled="page * PAGE_SIZE >= total" @click="changePage(1)">Next <ChevronRight :size="14" /></button></div></footer>
    </div>
    <p v-if="!auditItems.length" class="users-empty">No matching audit events.</p>
  </template>
</template>
