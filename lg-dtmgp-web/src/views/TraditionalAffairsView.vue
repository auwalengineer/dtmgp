<script setup lang="ts">
import { BadgeCheck, CircleAlert, Crown, Landmark } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import AllowancesEntitlementsSection from "./traditional/AllowancesEntitlementsSection.vue";
import AppointmentsSection from "./traditional/AppointmentsSection.vue";
import PetitionsDisputesSection from "./traditional/PetitionsDisputesSection.vue";
import RecognitionCertificationSection from "./traditional/RecognitionCertificationSection.vue";
import SuccessionSection from "./traditional/SuccessionSection.vue";
import TraditionalInstitutionsSection from "./traditional/TraditionalInstitutionsSection.vue";
import TraditionalReportsSection from "./traditional/TraditionalReportsSection.vue";
import TraditionalRulersSection from "./traditional/TraditionalRulersSection.vue";
import type { Dashboard } from "./traditional/types";

const TAB_LABELS = ["Traditional Institutions", "Traditional Rulers", "Appointments", "Succession", "Recognition & Certification", "Petitions & Disputes", "Allowances & Entitlements", "Reports"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = { "traditional-institutions": "Traditional Institutions", "traditional-rulers": "Traditional Rulers", appointments: "Appointments", succession: "Succession", "recognition-certification": "Recognition & Certification", "petitions-disputes": "Petitions & Disputes", "allowances-entitlements": "Allowances & Entitlements", reports: "Reports" };

const session = useSessionStore();
const route = useRoute();
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || TAB_LABELS[0]);
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) activeTab.value = mapped; });
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }

const dashboard = ref<Dashboard | null>(null);
const loading = ref(true);
const error = ref("");
async function loadDashboard() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try { dashboard.value = await apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.traditional.get_dashboard?company=${encodeURIComponent(session.activeLga)}`); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load the chieftaincy workspace"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadDashboard, { immediate: true });
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ shortLga() }}</p><h1>Chieftaincy & Traditional Institutions</h1><p>Traditional institutions, rulers, appointments, succession and dispute records</p></div></section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading chieftaincy records...</section>
  <template v-else-if="dashboard">
    <section class="hr-metrics" aria-label="Chieftaincy summary">
      <article><span class="hr-metric-icon green"><Landmark :size="19" /></span><div><small>Active institutions</small><strong>{{ dashboard.active_institutions }}</strong><p>{{ dashboard.vacant_stools }} vacant</p></div></article>
      <article><span class="hr-metric-icon blue"><Crown :size="19" /></span><div><small>Reigning rulers</small><strong>{{ dashboard.reigning_rulers }}</strong></div></article>
      <article><span class="hr-metric-icon gold"><BadgeCheck :size="19" /></span><div><small>Pending recognition</small><strong>{{ dashboard.pending_recognition }}</strong></div></article>
      <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Open petitions</small><strong>{{ dashboard.open_petitions }}</strong></div></article>
    </section>

    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="Chieftaincy and traditional institutions views"><button v-for="tab in TAB_LABELS" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button></nav>

      <TraditionalInstitutionsSection v-if="activeTab === 'Traditional Institutions'" :can-manage="dashboard.can_manage" />
      <TraditionalRulersSection v-else-if="activeTab === 'Traditional Rulers'" :can-manage="dashboard.can_manage" />
      <AppointmentsSection v-else-if="activeTab === 'Appointments'" :can-manage="dashboard.can_manage" />
      <SuccessionSection v-else-if="activeTab === 'Succession'" :can-manage="dashboard.can_manage" />
      <RecognitionCertificationSection v-else-if="activeTab === 'Recognition & Certification'" :can-manage="dashboard.can_manage" />
      <PetitionsDisputesSection v-else-if="activeTab === 'Petitions & Disputes'" :can-manage="dashboard.can_manage" />
      <AllowancesEntitlementsSection v-else-if="activeTab === 'Allowances & Entitlements'" :can-manage="dashboard.can_manage" />
      <TraditionalReportsSection v-else-if="activeTab === 'Reports'" />
    </section>
  </template>
</template>
