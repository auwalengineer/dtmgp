<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useSessionStore } from "@/stores/session";

import AllowancesEntitlementsSection from "./traditional/AllowancesEntitlementsSection.vue";
import AppointmentsSection from "./traditional/AppointmentsSection.vue";
import PetitionsDisputesSection from "./traditional/PetitionsDisputesSection.vue";
import RecognitionCertificationSection from "./traditional/RecognitionCertificationSection.vue";
import SuccessionSection from "./traditional/SuccessionSection.vue";
import TraditionalInstitutionsSection from "./traditional/TraditionalInstitutionsSection.vue";
import TraditionalReportsSection from "./traditional/TraditionalReportsSection.vue";
import TraditionalRulersSection from "./traditional/TraditionalRulersSection.vue";

const TAB_LABELS = ["Traditional Institutions", "Traditional Rulers", "Appointments", "Succession", "Recognition & Certification", "Petitions & Disputes", "Allowances & Entitlements", "Reports"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = { "traditional-institutions": "Traditional Institutions", "traditional-rulers": "Traditional Rulers", appointments: "Appointments", succession: "Succession", "recognition-certification": "Recognition & Certification", "petitions-disputes": "Petitions & Disputes", "allowances-entitlements": "Allowances & Entitlements", reports: "Reports" };

const session = useSessionStore();
const route = useRoute();
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || TAB_LABELS[0]);
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) activeTab.value = mapped; });
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ shortLga() }}</p><h1>Chieftaincy & Traditional Institutions</h1><p>Traditional institutions, rulers, appointments, succession and dispute records</p></div></section>

  <p class="users-empty" style="background:#fff;border:1px solid var(--line);margin-bottom:24px;text-align:left;padding:16px 20px">This domain isn't operational yet — no data model, permissions or APIs exist for chieftaincy and traditional institutions in the platform today. The sections below show what each planned page will cover once the domain is scoped and approved.</p>

  <section class="hr-workspace">
    <nav class="hr-tabs" aria-label="Chieftaincy and traditional institutions views"><button v-for="tab in TAB_LABELS" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button></nav>

    <TraditionalInstitutionsSection v-if="activeTab === 'Traditional Institutions'" />
    <TraditionalRulersSection v-else-if="activeTab === 'Traditional Rulers'" />
    <AppointmentsSection v-else-if="activeTab === 'Appointments'" />
    <SuccessionSection v-else-if="activeTab === 'Succession'" />
    <RecognitionCertificationSection v-else-if="activeTab === 'Recognition & Certification'" />
    <PetitionsDisputesSection v-else-if="activeTab === 'Petitions & Disputes'" />
    <AllowancesEntitlementsSection v-else-if="activeTab === 'Allowances & Entitlements'" />
    <TraditionalReportsSection v-else-if="activeTab === 'Reports'" />
  </section>
</template>
