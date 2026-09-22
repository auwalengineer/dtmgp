<script setup lang="ts">
import { Plus } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import ItemTabs from "../shared/ItemTabs.vue";
import type { DepartmentItem, Designation, FiscalYearRow, LgaProfile } from "./types";

const ITEM_LABELS: Record<string, string> = { lgas: "LGAs", "departments-units": "Departments & Units", designations: "Designations", "fiscal-years": "Fiscal Years" };
const DEFAULT_ITEM = "lgas";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const session = useSessionStore();
const lgas = ref<LgaProfile[]>([]);
const departments = ref<DepartmentItem[]>([]);
const designations = ref<Designation[]>([]);
const fiscalYears = ref<FiscalYearRow[]>([]);
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const formKind = ref<"department" | "designation" | "fiscal-year">("designation");
const form = ref<Record<string, string | number>>({});
const saving = ref(false);

const groups = computed(() => departments.value.filter((d) => d.is_group));
const units = computed(() => departments.value.filter((d) => !d.is_group));

async function load() {
  loading.value = true;
  error.value = "";
  const company = session.activeLga ? `?company=${encodeURIComponent(session.activeLga)}` : "";
  try {
    [lgas.value, departments.value, designations.value, fiscalYears.value] = await Promise.all([
      apiRequest<LgaProfile[]>("/api/method/dtmgp.api.v1.administration.list_lga_profiles"),
      apiRequest<DepartmentItem[]>(`/api/method/dtmgp.api.v1.governance.list_departments${company}`),
      apiRequest<Designation[]>("/api/method/dtmgp.api.v1.administration.list_reference_records?doctype=Designation"),
      apiRequest<FiscalYearRow[]>(`/api/method/dtmgp.api.v1.administration.list_reference_records?doctype=${encodeURIComponent("Fiscal Year")}`),
    ]);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load Organization Setup"; }
  finally { loading.value = false; }
}
watch(() => session.activeLga, load, { immediate: true });

async function toggleLga(lga: LgaProfile) {
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.administration.set_lga_profile_enabled", { method: "POST", body: JSON.stringify({ lga_code: lga.lga_code, enabled: lga.enabled ? 0 : 1 }) });
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update LGA"; }
}

function openForm(kind: typeof formKind.value) {
  formKind.value = kind;
  form.value = kind === "department"
    ? { company: session.activeLga, department_name: "", is_group: 0, parent_department: "" }
    : kind === "designation" ? { designation_name: "", description: "" }
    : { year: "", year_start_date: "", year_end_date: "" };
  showForm.value = true;
}

async function saveForm() {
  saving.value = true;
  error.value = "";
  try {
    if (formKind.value === "department") {
      await apiRequest("/api/method/dtmgp.api.v1.governance.save_department", { method: "POST", body: JSON.stringify({ values: form.value }) });
    } else {
      const doctype = formKind.value === "designation" ? "Designation" : "Fiscal Year";
      await apiRequest("/api/method/dtmgp.api.v1.administration.save_reference_record", { method: "POST", body: JSON.stringify({ doctype, values: form.value }) });
    }
    showForm.value = false;
    await load();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the record"; }
  finally { saving.value = false; }
}
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <p v-if="loading" class="users-empty">Loading...</p>
  <template v-else>
    <template v-if="activeItem === 'lgas'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Local Government Areas</h3></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>LGA</th><th>Code</th><th>Company</th><th>Status</th><th v-if="session.canManageSystemConfig"></th></tr></thead><tbody><tr v-for="lga in lgas" :key="lga.name"><td><strong>{{ lga.lga_name }}</strong></td><td>{{ lga.lga_code }}</td><td>{{ lga.company }}</td><td><span class="table-status" :class="lga.enabled ? 'success' : 'neutral'">{{ lga.enabled ? "Enabled" : "Disabled" }}</span></td><td v-if="session.canManageSystemConfig"><button class="secondary-action compact-action" @click="toggleLga(lga)">{{ lga.enabled ? "Disable" : "Enable" }}</button></td></tr></tbody></table></div>
    </template>

    <template v-else-if="activeItem === 'departments-units'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Departments</h3><button class="secondary-action" @click="openForm('department')"><Plus :size="15" /> New department</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Department</th><th>LGA</th><th>Status</th></tr></thead><tbody><tr v-for="item in groups.length ? groups : departments" :key="item.name"><td><strong>{{ item.department_name }}</strong></td><td>{{ item.company.replace(" Local Government Area", " LGA") }}</td><td><span class="table-status" :class="item.disabled ? 'neutral' : 'success'">{{ item.disabled ? "Disabled" : "Active" }}</span></td></tr></tbody></table><p v-if="!departments.length" class="users-empty">No departments recorded for this LGA yet.</p></div>
      <template v-if="units.length">
        <div class="directory-toolbar"><h3 style="margin:0;flex:1">Units</h3></div>
        <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Unit</th><th>Parent department</th><th>Status</th></tr></thead><tbody><tr v-for="item in units" :key="item.name"><td><strong>{{ item.department_name }}</strong></td><td>{{ item.parent_department || "—" }}</td><td><span class="table-status" :class="item.disabled ? 'neutral' : 'success'">{{ item.disabled ? "Disabled" : "Active" }}</span></td></tr></tbody></table></div>
      </template>
    </template>

    <template v-else-if="activeItem === 'designations'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Designations</h3><button class="secondary-action" @click="openForm('designation')"><Plus :size="15" /> New designation</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Designation</th><th>Description</th></tr></thead><tbody><tr v-for="item in designations" :key="item.name"><td><strong>{{ item.designation_name }}</strong></td><td>{{ item.description || "—" }}</td></tr></tbody></table></div>
    </template>

    <template v-else-if="activeItem === 'fiscal-years'">
      <div class="directory-toolbar"><h3 style="margin:0;flex:1">Fiscal years</h3><button v-if="session.canManageSystemConfig" class="secondary-action" @click="openForm('fiscal-year')"><Plus :size="15" /> New fiscal year</button></div>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Year</th><th>Start</th><th>End</th><th>Status</th></tr></thead><tbody><tr v-for="item in fiscalYears" :key="item.name"><td><strong>{{ item.year }}</strong></td><td>{{ item.year_start_date }}</td><td>{{ item.year_end_date }}</td><td><span class="table-status" :class="item.disabled ? 'neutral' : 'success'">{{ item.disabled ? "Disabled" : "Active" }}</span></td></tr></tbody></table></div>
      <p v-if="!session.canManageSystemConfig" class="users-empty">Fiscal years drive every LGA's ledger, so only state administrators can create or change them.</p>
    </template>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveForm">
    <template v-if="formKind === 'department'"><h2>New department</h2><label>Department name<input v-model="form.department_name" required /></label><label>Group?<select v-model.number="form.is_group"><option :value="0">No — this is a unit/office</option><option :value="1">Yes — this is a department (can contain units)</option></select></label><label>Parent department<input v-model="form.parent_department" placeholder="Optional" /></label></template>
    <template v-else-if="formKind === 'designation'"><h2>New designation</h2><label>Name<input v-model="form.designation_name" required /></label><label>Description<textarea v-model="form.description"></textarea></label></template>
    <template v-else><h2>New fiscal year</h2><label>Year label<input v-model="form.year" required placeholder="e.g. 2027" /></label><label>Start date<input v-model="form.year_start_date" type="date" required /></label><label>End date<input v-model="form.year_end_date" type="date" required /></label></template>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p>
    <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save" }}</button></footer>
  </form></div>
</template>
