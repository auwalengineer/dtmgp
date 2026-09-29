<script setup lang="ts">
import { FilePlus2, History, ShieldCheck } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { today } from "./types";
import type { AuditQuery } from "./types";

const props = defineProps<{ auditQueries: AuditQuery[]; canManage: boolean }>();
defineEmits<{ "new-query": []; "advance-query": [name: string, target: string] }>();

const NEXT_STATUS: Record<string, string> = { Open: "Response Submitted", "Response Submitted": "Under Review", "Under Review": "Resolved", Resolved: "Closed" };
const ITEM_LABELS: Record<string, string> = { "audit-queries": "Audit Queries", "audit-responses": "Audit Responses", "financial-exceptions": "Financial Exceptions", "approval-history": "Approval History", "financial-audit-trail": "Financial Audit Trail" };
const DEFAULT_ITEM = "audit-queries";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const respondedQueries = computed(() => props.auditQueries.filter((q) => q.status !== "Open"));
const exceptionQueries = computed(() => props.auditQueries.filter((q) => ["High", "Critical"].includes(q.severity) || (q.response_due_date && q.response_due_date < today() && !["Resolved", "Closed"].includes(q.status))));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'audit-queries'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Audit queries</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-query')"><FilePlus2 :size="15" /> New audit query</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Subject</th><th>Area</th><th>Severity</th><th>Due</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in auditQueries" :key="item.name" v-record="{ doctype: 'DTMGP Audit Query', name: item.name }"><td><strong>{{ item.subject }}</strong></td><td>{{ item.query_type }}</td><td><span class="table-status" :class="['High', 'Critical'].includes(item.severity) ? 'neutral' : 'success'">{{ item.severity }}</span></td><td>{{ item.response_due_date }}</td><td><span class="table-status" :class="item.status === 'Closed' ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="$emit('advance-query', item.name, NEXT_STATUS[item.status])">Advance to {{ NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!auditQueries.length" class="users-empty">No audit queries recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'audit-responses'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Subject</th><th>Area</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in respondedQueries" :key="item.name" v-record="{ doctype: 'DTMGP Audit Query', name: item.name }"><td><strong>{{ item.subject }}</strong></td><td>{{ item.query_type }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage && NEXT_STATUS[item.status]" class="secondary-action compact-action" @click="$emit('advance-query', item.name, NEXT_STATUS[item.status])">Advance to {{ NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!respondedQueries.length" class="users-empty">No queries with a response yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'financial-exceptions'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Subject</th><th>Severity</th><th>Due</th><th>Status</th></tr></thead><tbody><tr v-for="item in exceptionQueries" :key="item.name" v-record="{ doctype: 'DTMGP Audit Query', name: item.name }"><td><strong>{{ item.subject }}</strong></td><td>{{ item.severity }}</td><td>{{ item.response_due_date }}</td><td><span class="table-status neutral">{{ item.status }}</span></td></tr></tbody></table><p v-if="!exceptionQueries.length" class="users-empty">No high-severity or overdue audit queries right now.</p></div>
  </template>

  <template v-else-if="activeItem === 'approval-history'">
    <PreviewCard :icon="ShieldCheck" title="Approval history" body="A history of who approved which transaction against which approval limit isn't exposed yet — approval limits are enforced server-side but aren't logged to a browsable list." />
  </template>

  <template v-else-if="activeItem === 'financial-audit-trail'">
    <PreviewCard :icon="History" title="Financial audit trail" body="Financial document lifecycle events are recorded append-only in the platform's audit trail, but there is no listing API exposed for this UI yet." />
  </template>
</template>
