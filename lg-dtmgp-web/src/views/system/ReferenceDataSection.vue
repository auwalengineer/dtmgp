<script setup lang="ts">
import { FolderTree, Plus } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import type { DocumentNumberingEntry, LocationRow } from "./types";

const ITEM_LABELS: Record<string, string> = { "document-numbering": "Document Numbering", "status-definitions": "Status Definitions", categories: "Categories", locations: "Locations", "other-reference-data": "Other Reference Data" };
const DEFAULT_ITEM = "document-numbering";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const numbering = ref<DocumentNumberingEntry[]>([]);
const locations = ref<LocationRow[]>([]);
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const form = ref<Record<string, string | number>>({});
const saving = ref(false);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    [numbering.value, locations.value] = await Promise.all([
      apiRequest<DocumentNumberingEntry[]>("/api/method/dtmgp.api.v1.administration.get_document_numbering_reference"),
      apiRequest<LocationRow[]>("/api/method/dtmgp.api.v1.administration.list_reference_records?doctype=Location"),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load Reference Data"; }
  finally { loading.value = false; }
}
load();

function openForm() { form.value = { location_name: "", is_group: 0 }; showForm.value = true; }
async function saveForm() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.administration.save_reference_record", { method: "POST", body: JSON.stringify({ doctype: "Location", values: form.value }) });
    showForm.value = false;
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the location"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>
  <template v-else>
    <template v-if="activeItem === 'document-numbering'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Document numbering</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Record type</th><th>Identifier pattern</th></tr></thead><tbody><tr v-for="item in numbering" :key="item.doctype"><td>{{ item.doctype }}</td><td><code>{{ item.autoname || "system-generated" }}</code></td></tr></tbody></table></div>
      <p class="users-empty">Sequences shown here are live, in-code configuration, not editable — identifiers are immutable and never recycled once assigned (see docs/naming-and-coding-conventions.md).</p>
    </template>

    <template v-else-if="activeItem === 'locations'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Locations</h3><button class="secondary-action" @click="openForm"><Plus :size="15" /> New location</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Location</th><th>Parent</th><th>Coordinates</th></tr></thead><tbody><tr v-for="item in locations" :key="item.name"><td><strong>{{ item.location_name }}</strong>{{ item.is_group ? " (group)" : "" }}</td><td>{{ item.parent_location || "—" }}</td><td>{{ item.latitude && item.longitude ? `${item.latitude}, ${item.longitude}` : "—" }}</td></tr></tbody></table><p v-if="!locations.length" class="users-empty">No locations recorded yet — these feed the Projects module's Project Location and Asset Location fields.</p></div>
    </template>

    <template v-else>
      <PreviewCard :icon="FolderTree" :title="ITEM_LABELS[activeItem]" body="There's no concrete record type backing this yet — it isn't part of any domain's data model, so building a management screen for it would be decorative rather than real." />
    </template>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveForm">
    <h2>New location</h2>
    <label>Name<input v-model="form.location_name" required /></label>
    <label>Group?<select v-model.number="form.is_group"><option :value="0">No — this is a specific location</option><option :value="1">Yes — this groups other locations</option></select></label>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save" }}</button></footer>
  </form></div>
</template>
