<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/stores/session";

import CommunicationSetupSection from "./system/CommunicationSetupSection.vue";
import OrganizationSetupSection from "./system/OrganizationSetupSection.vue";
import ReferenceDataSection from "./system/ReferenceDataSection.vue";
import SecurityAuditSection from "./system/SecurityAuditSection.vue";
import SystemOperationsSection from "./system/SystemOperationsSection.vue";
import UserManagementSection from "./system/UserManagementSection.vue";
import WorkflowSetupSection from "./system/WorkflowSetupSection.vue";

const TAB_LABELS = ["User Management", "Organization Setup", "Workflow Setup", "Communication Setup", "Reference Data", "Security & Audit", "System Operations"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = {
  "user-management": "User Management",
  "organization-setup": "Organization Setup",
  "workflow-setup": "Workflow Setup",
  "communication-setup": "Communication Setup",
  "reference-data": "Reference Data",
  "security-audit": "Security & Audit",
  "system-operations": "System Operations",
};

const session = useSessionStore();
const route = useRoute();
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || TAB_LABELS[0]);
const visibleTabs = computed(() => TAB_LABELS.filter((tab) =>
  (!["Workflow Setup", "Communication Setup", "Reference Data", "Security & Audit"].includes(tab) || session.canManageSystemConfig)
  && (tab !== "System Operations" || session.canManageSystemOperations),
));

function selectTab(tab: Tab) { activeTab.value = tab; }
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) activeTab.value = mapped; });
watch(visibleTabs, (tabs) => { if (!tabs.includes(activeTab.value) && tabs.length) activeTab.value = tabs[0]; });
function shortLga() { return session.activeLga ? session.activeLga.replace(" Local Government Area", " LGA") : "Statewide"; }
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ shortLga() }}</p><h1>System Administration</h1><p>Users, organization setup, workflow configuration, reference data, security and audit</p></div></section>

  <section class="hr-workspace">
    <nav class="hr-tabs" aria-label="System Administration views"><button v-for="tab in visibleTabs" :key="tab" :class="{ active: activeTab === tab }" @click="selectTab(tab)">{{ tab }}</button></nav>

    <UserManagementSection v-if="activeTab === 'User Management'" />
    <OrganizationSetupSection v-else-if="activeTab === 'Organization Setup'" />
    <WorkflowSetupSection v-else-if="activeTab === 'Workflow Setup'" />
    <CommunicationSetupSection v-else-if="activeTab === 'Communication Setup'" />
    <ReferenceDataSection v-else-if="activeTab === 'Reference Data'" />
    <SecurityAuditSection v-else-if="activeTab === 'Security & Audit'" />
    <SystemOperationsSection v-else-if="activeTab === 'System Operations'" />
  </section>
</template>
