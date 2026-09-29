<script setup lang="ts">
import { FilePlus2 } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { Institution, Petition } from "./types";
import { nextInChain, PETITION_CHAIN, today } from "./types";

interface PetitionDocument { name: string; file_name: string; file_url: string; is_private: number; creation: string }

defineProps<{ canManage: boolean }>();

const session = useSessionStore();
const ITEM_LABELS: Record<string, string> = { "new-petitions": "New Petitions", "petition-register": "Petition Register", "dispute-cases": "Dispute Cases", hearings: "Hearings", "evidence-documents": "Evidence & Documents", "decisions-resolutions": "Decisions & Resolutions", appeals: "Appeals" };
const DEFAULT_ITEM = "petition-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const petitions = ref<Petition[]>([]);
const institutions = ref<Institution[]>([]);
const loading = ref(true);
const error = ref("");
async function loadAll() {
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [petitions.value, institutions.value] = await Promise.all([
      apiRequest<{ items: Petition[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Chieftaincy Petition")}&company=${company}&page_size=100`).then((r) => r.items),
      apiRequest<{ items: Institution[] }>(`/api/method/dtmgp.api.v1.traditional.list_records?doctype=${encodeURIComponent("DTMGP Traditional Institution")}&company=${company}&page_size=100`).then((r) => r.items),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load petitions"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, loadAll, { immediate: true });

const disputeCases = computed(() => petitions.value.filter((p) => ["Council Hearing", "Panel of Inquiry", "Exco Review"].includes(p.status)));
const hearings = computed(() => petitions.value.filter((p) => p.hearing_date));
const decisions = computed(() => petitions.value.filter((p) => ["Decided", "Appealed", "Closed"].includes(p.status)));
const appeals = computed(() => petitions.value.filter((p) => p.status === "Appealed"));

async function advance(name: string) {
  const record = petitions.value.find((p) => p.name === name);
  const target = record && nextInChain(PETITION_CHAIN, record.status);
  if (!target) return;
  error.value = "";
  try {
    if (target === "Decided") {
      const decision = window.prompt("Decision (required to mark this petition Decided)");
      if (!decision) return;
      await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Chieftaincy Petition", name, values: { decision } }) });
    }
    await apiRequest("/api/method/dtmgp.api.v1.traditional.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Chieftaincy Petition", name, target_status: target }) });
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to advance the petition"; }
}

const selectedPetition = ref("");
const documents = ref<PetitionDocument[]>([]);
const documentsLoading = ref(false);
watch(selectedPetition, async (name) => {
  if (!name) { documents.value = []; return; }
  documentsLoading.value = true;
  try { documents.value = await apiRequest<PetitionDocument[]>(`/api/method/dtmgp.api.v1.traditional.list_petition_documents?petition=${encodeURIComponent(name)}`); }
  finally { documentsLoading.value = false; }
});

const showForm = ref(false);
const saving = ref(false);
const form = ref<Record<string, string>>({});
function openCreate() { form.value = { institution: "", respondent_institution: "", petitioner_name: "", petition_type: "Rival Claim", petition_date: today(), description: "" }; showForm.value = true; activeItem.value = "new-petitions"; }
async function savePetition() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.traditional.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Chieftaincy Petition", values: { ...form.value, company: session.activeLga } }) });
    showForm.value = false;
    await loadAll();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the petition"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>

  <template v-if="activeItem === 'new-petitions'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">File a new petition</h3><button v-if="canManage" class="secondary-action" @click="openCreate"><FilePlus2 :size="15" /> New petition</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th>Type</th><th>Filed</th></tr></thead><tbody><tr v-for="item in petitions.filter(p => p.status === 'Filed')" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.petition_type }}</td><td>{{ item.petition_date }}</td></tr></tbody></table><p v-if="!petitions.filter(p => p.status === 'Filed').length" class="users-empty">No newly filed petitions.</p></div>
  </template>

  <template v-else-if="activeItem === 'petition-register'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th>Type</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in petitions" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.petition_type }}</td><td><span class="table-status" :class="['Decided', 'Closed'].includes(item.status) ? 'success' : 'neutral'">{{ item.status }}</span></td><td><button v-if="canManage && nextInChain(PETITION_CHAIN, item.status)" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="loading" class="users-empty">Loading...</p><p v-else-if="!petitions.length" class="users-empty">No petitions recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'dispute-cases'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th>Stage</th><th></th></tr></thead><tbody><tr v-for="item in disputeCases" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Advance</button></td></tr></tbody></table><p v-if="!disputeCases.length" class="users-empty">No disputes currently in hearing or review.</p></div>
  </template>

  <template v-else-if="activeItem === 'hearings'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th>Hearing date</th></tr></thead><tbody><tr v-for="item in hearings" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.hearing_date }}</td></tr></tbody></table><p v-if="!hearings.length" class="users-empty">No hearings scheduled yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'evidence-documents'">
    <div class="directory-toolbar"><label style="flex:1;max-width:360px">Petition<select v-model="selectedPetition"><option value="">Select a petition</option><option v-for="item in petitions" :key="item.name" :value="item.name">{{ item.petitioner_name }} — {{ item.institution }}</option></select></label></div>
    <p v-if="!selectedPetition" class="users-empty">Select a petition above to view its evidence and documents.</p>
    <div v-else class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Document</th><th>Visibility</th><th>Uploaded</th></tr></thead><tbody><tr v-for="row in documents" :key="row.name"><td><a :href="row.file_url" target="_blank" rel="noopener">{{ row.file_name }}</a></td><td>{{ row.is_private ? "Private" : "Public" }}</td><td>{{ row.creation }}</td></tr></tbody></table><p v-if="documentsLoading" class="users-empty">Loading documents...</p><p v-else-if="!documents.length" class="users-empty">No documents attached to this petition yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'decisions-resolutions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th>Decision</th><th>Date</th></tr></thead><tbody><tr v-for="item in decisions" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td>{{ item.decision || '-' }}</td><td>{{ item.decision_date || '-' }}</td></tr></tbody></table><p v-if="!decisions.length" class="users-empty">No decisions recorded yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'appeals'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Petitioner</th><th>Institution</th><th></th></tr></thead><tbody><tr v-for="item in appeals" :key="item.name" v-record="{ doctype: 'DTMGP Chieftaincy Petition', name: item.name }"><td><strong>{{ item.petitioner_name }}</strong></td><td>{{ item.institution }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="advance(item.name)">Close</button></td></tr></tbody></table><p v-if="!appeals.length" class="users-empty">No petitions currently under appeal.</p></div>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="savePetition"><h2>New petition</h2><div class="form-grid">
    <label>Institution<select v-model="form.institution" required><option value="" disabled>Select institution</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label>Respondent institution<select v-model="form.respondent_institution"><option value="">None</option><option v-for="item in institutions" :key="item.name" :value="item.name">{{ item.institution_name }}</option></select></label>
    <label class="full-field">Petitioner name<input v-model="form.petitioner_name" required /></label>
    <label>Petition type<select v-model="form.petition_type"><option>Rival Claim</option><option>Eligibility Challenge</option><option>Misconduct</option><option>Other</option></select></label>
    <label>Petition date<input v-model="form.petition_date" type="date" required /></label>
    <label class="full-field">Description<textarea v-model="form.description" required></textarea></label>
  </div><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save petition" }}</button></footer></form></div>
</template>
