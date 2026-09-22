<script setup lang="ts">
import { Camera, FolderKanban, HardHat, TriangleAlert } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest, uploadFile } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import AssetsSection from "./projects/AssetsSection.vue";
import ContractorsSection from "./projects/ContractorsSection.vue";
import FieldMonitoringSection from "./projects/FieldMonitoringSection.vue";
import FleetManagementSection from "./projects/FleetManagementSection.vue";
import MapsSection from "./projects/MapsSection.vue";
import ProgressMonitoringSection from "./projects/ProgressMonitoringSection.vue";
import ProjectPlanningSection from "./projects/ProjectPlanningSection.vue";
import ProjectsReportsSection from "./projects/ProjectsReportsSection.vue";
import ProjectsSection from "./projects/ProjectsSection.vue";
import { today } from "./projects/types";
import type { AssetMaintenanceRecord, AssetMovementRecord, AssetRecord, AssetVerificationRecord, Contractor, ContractorPerformance, Dashboard, InspectionRecord, MapsData, Options, Project, ReportsData, Task, VehicleLogRecord, VehicleRecord } from "./projects/types";

const TAB_LABELS = ["Projects", "Project Planning", "Contractors", "Field Monitoring", "Progress Monitoring", "Assets", "Fleet Management", "Maps", "Reports"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = { projects: "Projects", "project-planning": "Project Planning", contractors: "Contractors", "field-monitoring": "Field Monitoring", "progress-monitoring": "Progress Monitoring", assets: "Assets", "fleet-management": "Fleet Management", maps: "Maps", reports: "Reports" };

const session = useSessionStore();
const route = useRoute();
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || TAB_LABELS[0]);
const dashboard = ref<Dashboard | null>(null);
const options = ref<Options>({ employees: [], locations: [], asset_categories: [], items: [], open_projects: [] });
const projects = ref<Project[]>([]);
const tasks = ref<Task[]>([]);
const milestones = ref<Task[]>([]);
const inspections = ref<InspectionRecord[]>([]);
const assets = ref<AssetRecord[]>([]);
const assetMovements = ref<AssetMovementRecord[]>([]);
const assetMaintenance = ref<AssetMaintenanceRecord[]>([]);
const assetVerifications = ref<AssetVerificationRecord[]>([]);
const vehicles = ref<VehicleRecord[]>([]);
const vehicleLogs = ref<VehicleLogRecord[]>([]);
const contractors = ref<Contractor[]>([]);
const contractorPerformance = ref<ContractorPerformance[]>([]);
const mapsData = ref<MapsData>({ projects: [], assets: [], inspections: [] });
const reportsData = ref<ReportsData | null>(null);
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const formKind = ref<"project" | "task" | "inspection" | "asset" | "asset-verification" | "asset-movement" | "vehicle" | "vehicle-log">("project");
const form = ref<Record<string, string | number>>({});
const photoFile = ref<File | null>(null);
const saving = ref(false);

function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }
async function listRecords<T>(doctype: string): Promise<T[]> {
  const result = await apiRequest<{ items: T[] }>(`/api/method/dtmgp.api.v1.projects.list_records?doctype=${encodeURIComponent(doctype)}&${scopeQuery()}&page_size=100`);
  return result.items;
}

async function loadModule() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    [dashboard.value, options.value] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.projects.get_dashboard?${scopeQuery()}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.projects.get_form_options?${scopeQuery()}`),
    ]);
    await selectTab(activeTab.value);
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load the projects workspace"; }
  finally { loading.value = false; }
}

async function loadProjects() { projects.value = (await apiRequest<{ items: Project[] }>(`/api/method/dtmgp.api.v1.projects.list_projects?${scopeQuery()}&view=register&page_size=100`)).items; }
async function loadTasks() { tasks.value = (await apiRequest<{ items: Task[] }>(`/api/method/dtmgp.api.v1.projects.list_tasks?${scopeQuery()}&is_milestone=0&page_size=100`)).items; }
async function loadMilestones() { milestones.value = (await apiRequest<{ items: Task[] }>(`/api/method/dtmgp.api.v1.projects.list_tasks?${scopeQuery()}&is_milestone=1&page_size=100`)).items; }
async function loadInspections() { inspections.value = await listRecords<InspectionRecord>("DTMGP Project Inspection"); }
async function loadContractors() {
  [contractors.value, contractorPerformance.value] = await Promise.all([
    apiRequest<{ items: Contractor[] }>("/api/method/dtmgp.api.v1.projects.list_contractors?page_size=100").then((r) => r.items),
    apiRequest<{ items: ContractorPerformance[] }>(`/api/method/dtmgp.api.v1.projects.get_contractor_performance?${scopeQuery()}`).then((r) => r.items),
  ]);
}
async function loadAssets() {
  [assets.value, assetMovements.value, assetMaintenance.value, assetVerifications.value] = await Promise.all([
    listRecords<AssetRecord>("Asset"), listRecords<AssetMovementRecord>("Asset Movement"),
    listRecords<AssetMaintenanceRecord>("Asset Maintenance"), listRecords<AssetVerificationRecord>("DTMGP Asset Verification"),
  ]);
}
async function loadFleet() {
  [vehicles.value, vehicleLogs.value] = await Promise.all([
    listRecords<VehicleRecord>("Vehicle"),
    apiRequest<{ items: VehicleLogRecord[] }>(`/api/method/dtmgp.api.v1.projects.list_vehicle_logs?${scopeQuery()}&page_size=100`).then((r) => r.items),
  ]);
}
async function loadMaps() { mapsData.value = await apiRequest<MapsData>(`/api/method/dtmgp.api.v1.projects.get_maps_data?${scopeQuery()}`); }
async function loadReports() { reportsData.value = await apiRequest<ReportsData>(`/api/method/dtmgp.api.v1.projects.get_reports?${scopeQuery()}`); }

async function selectTab(tab: Tab) {
  activeTab.value = tab;
  if (tab === "Projects") await loadProjects();
  else if (tab === "Project Planning") await Promise.all([loadProjects(), loadTasks(), loadMilestones()]);
  else if (tab === "Contractors") await loadContractors();
  else if (tab === "Field Monitoring") await Promise.all([loadInspections(), loadProjects()]);
  else if (tab === "Progress Monitoring") await Promise.all([loadProjects(), loadMilestones()]);
  else if (tab === "Assets") await loadAssets();
  else if (tab === "Fleet Management") await loadFleet();
  else if (tab === "Maps") await loadMaps();
  else if (tab === "Reports") await loadReports();
}
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) selectTab(mapped); });
watch(() => session.activeLga, loadModule, { immediate: true });

function openForm(kind: typeof formKind.value, initial: Record<string, string | number>) { formKind.value = kind; form.value = initial; photoFile.value = null; showForm.value = true; }

async function saveForm() {
  saving.value = true;
  error.value = "";
  try {
    if (formKind.value === "project") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_project", { method: "POST", body: JSON.stringify({ values: { ...form.value, company: session.activeLga } }) }); await loadProjects(); }
    else if (formKind.value === "task") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_task", { method: "POST", body: JSON.stringify({ values: form.value }) }); await Promise.all([loadTasks(), loadMilestones()]); }
    else if (formKind.value === "inspection") {
      const result = await apiRequest<{ name: string }>("/api/method/dtmgp.api.v1.projects.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Project Inspection", values: { ...form.value, company: session.activeLga } }) });
      if (photoFile.value) await uploadFile(photoFile.value, { doctype: "DTMGP Project Inspection", docname: result.name, fieldname: "photo_evidence" });
      await loadInspections();
    }
    else if (formKind.value === "asset") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_record", { method: "POST", body: JSON.stringify({ doctype: "Asset", values: { ...form.value, company: session.activeLga } }) }); await loadAssets(); }
    else if (formKind.value === "asset-movement") {
      const { purpose, transaction_date, asset, source_location, target_location, from_employee, to_employee } = form.value as Record<string, string>;
      const created = await apiRequest<{ name: string }>("/api/method/dtmgp.api.v1.projects.save_record", { method: "POST", body: JSON.stringify({ doctype: "Asset Movement", values: { company: session.activeLga, purpose, transaction_date, assets: [{ asset, source_location, target_location, from_employee, to_employee, company: session.activeLga }] } }) });
      await apiRequest("/api/method/dtmgp.api.v1.projects.submit_record", { method: "POST", body: JSON.stringify({ doctype: "Asset Movement", name: created.name }) });
      await loadAssets();
    }
    else if (formKind.value === "asset-verification") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Asset Verification", values: { ...form.value, company: session.activeLga } }) }); await loadAssets(); }
    else if (formKind.value === "vehicle") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_record", { method: "POST", body: JSON.stringify({ doctype: "Vehicle", values: { ...form.value, company: session.activeLga } }) }); await loadFleet(); }
    else if (formKind.value === "vehicle-log") { await apiRequest("/api/method/dtmgp.api.v1.projects.save_vehicle_log", { method: "POST", body: JSON.stringify({ values: form.value }) }); await loadFleet(); }
    showForm.value = false;
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save the record"; }
  finally { saving.value = false; }
}

async function transitionProject(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.projects.transition_record", { method: "POST", body: JSON.stringify({ doctype: "Project", name, target_status: target }) }); await loadProjects(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update the project"; } }
async function transitionInspection(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.projects.transition_record", { method: "POST", body: JSON.stringify({ doctype: "DTMGP Project Inspection", name, target_status: target }) }); await loadInspections(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update the inspection"; } }
async function setContractorHold(supplier: string, onHold: boolean) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.projects.set_contractor_hold", { method: "POST", body: JSON.stringify({ supplier, on_hold: onHold ? 1 : 0 }) }); await loadContractors(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update the contractor"; } }
async function submitAsset(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.projects.submit_record", { method: "POST", body: JSON.stringify({ doctype: "Asset", name }) }); await loadAssets(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to submit the asset"; } }
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ shortLga() }}</p><h1>Projects, Assets & Field Monitoring</h1><p>Project register, planning, contractors, field inspections, progress, assets and fleet</p></div></section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading projects workspace...</section>
  <template v-else-if="dashboard">
    <section class="finance-metrics" aria-label="Projects summary">
      <article><span class="hr-metric-icon green"><FolderKanban :size="19" /></span><div><small>Ongoing projects</small><strong>{{ dashboard.projects.ongoing }}</strong><p>{{ dashboard.projects.delayed }} delayed</p></div></article>
      <article><span class="hr-metric-icon red"><TriangleAlert :size="19" /></span><div><small>Open inspections</small><strong>{{ dashboard.inspections.open }}</strong><p>{{ dashboard.inspections.exceptions }} exceptions</p></div></article>
      <article><span class="hr-metric-icon blue"><HardHat :size="19" /></span><div><small>Registered assets</small><strong>{{ dashboard.assets.registered }}</strong><p>Submitted asset records</p></div></article>
      <article><span class="hr-metric-icon gold"><Camera :size="19" /></span><div><small>Fleet vehicles</small><strong>{{ dashboard.fleet.vehicles }}</strong><p>{{ dashboard.fleet.insurance_due }} insurance renewals due soon</p></div></article>
    </section>

    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="Projects, assets and field monitoring views"><button v-for="tab in TAB_LABELS" :key="tab" :class="{ active: activeTab === tab }" @click="selectTab(tab)">{{ tab }}</button></nav>

      <ProjectsSection v-if="activeTab === 'Projects'" :projects="projects" :can-manage="dashboard.can_manage" @new-project="openForm('project', { project_name: '', status: 'Open', priority: 'Medium', expected_start_date: today(), expected_end_date: today() })" @transition="transitionProject" />
      <ProjectPlanningSection v-else-if="activeTab === 'Project Planning'" :projects="projects" :tasks="tasks" :milestones="milestones" :options="options" :can-manage="dashboard.can_manage" @new-task="(isMilestone) => openForm('task', { project: '', subject: '', is_milestone: isMilestone, status: 'Open', priority: 'Medium', exp_start_date: today(), exp_end_date: today() })" @save-project="(name, values) => apiRequest('/api/method/dtmgp.api.v1.projects.save_project', { method: 'POST', body: JSON.stringify({ name, values }) }).then(loadProjects)" />
      <ContractorsSection v-else-if="activeTab === 'Contractors'" :contractors="contractors" :performance="contractorPerformance" :can-manage="dashboard.can_manage" @set-hold="setContractorHold" />
      <FieldMonitoringSection v-else-if="activeTab === 'Field Monitoring'" :inspections="inspections" :can-manage="dashboard.can_manage" @new-inspection="openForm('inspection', { project: '', scheduled_date: today(), status: 'Scheduled', latitude: '', longitude: '', findings: '', recommendation: '' })" @transition="transitionInspection" />
      <ProgressMonitoringSection v-else-if="activeTab === 'Progress Monitoring'" :projects="projects" :milestones="milestones" />
      <AssetsSection v-else-if="activeTab === 'Assets'" :assets="assets" :asset-movements="assetMovements" :asset-maintenance="assetMaintenance" :asset-verifications="assetVerifications" :options="options" :can-manage="dashboard.can_manage" @new-asset="openForm('asset', { asset_name: '', item_code: '', asset_category: '', location: '', purchase_date: today(), gross_purchase_amount: 0 })" @new-verification="openForm('asset-verification', { asset: '', verification_date: today(), condition: 'Good', remarks: '' })" @new-movement="(purpose) => openForm('asset-movement', { purpose, transaction_date: today(), asset: '', source_location: '', target_location: '', from_employee: '', to_employee: '' })" @submit-asset="submitAsset" />
      <FleetManagementSection v-else-if="activeTab === 'Fleet Management'" :vehicles="vehicles" :vehicle-logs="vehicleLogs" :can-manage="dashboard.can_manage" @new-vehicle="openForm('vehicle', { license_plate: '', make: '', model: '', last_odometer: 0, fuel_type: 'Petrol', uom: 'Nos' })" @new-log="openForm('vehicle-log', { license_plate: '', date: today(), odometer: 0, fuel_qty: 0, price: 0 })" />
      <MapsSection v-else-if="activeTab === 'Maps'" :maps-data="mapsData" />
      <ProjectsReportsSection v-else-if="activeTab === 'Reports'" :reports="reportsData" />
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal finance-modal" @submit.prevent="saveForm">
    <template v-if="formKind === 'project'"><h2>New project</h2><div class="form-grid"><label class="full-field">Project name<input v-model="form.project_name" required /></label><label>Priority<select v-model="form.priority"><option>Low</option><option>Medium</option><option>High</option></select></label><label>Funding source<select v-model="form.dtmgp_funding_source"><option value="">Select source</option><option>State</option><option>Federal</option><option>Donor</option><option>LGA Counterpart</option><option>Other</option></select></label><label>Location<select v-model="form.dtmgp_location"><option value="">Select location</option><option v-for="loc in options.locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option></select></label><label>Expected start<input v-model="form.expected_start_date" type="date" /></label><label>Expected end<input v-model="form.expected_end_date" type="date" /></label></div></template>

    <template v-else-if="formKind === 'task'"><h2>New task</h2><div class="form-grid"><label class="full-field">Project<select v-model="form.project" required><option value="" disabled>Select project</option><option v-for="p in options.open_projects" :key="p.name" :value="p.name">{{ p.project_name }}</option></select></label><label class="full-field">Subject<input v-model="form.subject" required /></label><label>Milestone<select v-model="form.is_milestone"><option :value="0">No — work plan item</option><option :value="1">Yes — milestone</option></select></label><label>Priority<select v-model="form.priority"><option>Low</option><option>Medium</option><option>High</option><option>Urgent</option></select></label><label>Start<input v-model="form.exp_start_date" type="date" /></label><label>End<input v-model="form.exp_end_date" type="date" /></label></div></template>

    <template v-else-if="formKind === 'inspection'"><h2>New inspection</h2><div class="form-grid"><label class="full-field">Project<select v-model="form.project" required><option value="" disabled>Select project</option><option v-for="p in options.open_projects" :key="p.name" :value="p.name">{{ p.project_name }}</option></select></label><label>Scheduled date<input v-model="form.scheduled_date" type="date" required /></label><label>Inspector<select v-model="form.inspector"><option value="">Select inspector</option><option v-for="e in options.employees" :key="e.name" :value="e.name">{{ e.employee_name }}</option></select></label><label>Latitude<input v-model.number="form.latitude" type="number" step="0.000001" placeholder="e.g. 7.733" /></label><label>Longitude<input v-model.number="form.longitude" type="number" step="0.000001" placeholder="e.g. 8.521" /></label><label>Photo evidence<input type="file" accept="image/*" @change="photoFile = ($event.target as HTMLInputElement).files?.[0] || null" /></label><label class="full-field">Findings<textarea v-model="form.findings"></textarea></label></div></template>

    <template v-else-if="formKind === 'asset'"><h2>New asset</h2><div class="form-grid"><label>Asset name<input v-model="form.asset_name" required /></label><label>Fixed asset item<select v-model="form.item_code" required><option value="" disabled>Select item</option><option v-for="i in options.items" :key="i.name" :value="i.name">{{ i.item_name }}</option></select></label><label>Category<select v-model="form.asset_category" required><option value="" disabled>Select category</option><option v-for="c in options.asset_categories" :key="c">{{ c }}</option></select></label><label>Location<select v-model="form.location" required><option value="" disabled>Select location</option><option v-for="loc in options.locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option></select></label><label>Purchase date<input v-model="form.purchase_date" type="date" required /></label><label>Gross purchase amount<input v-model.number="form.gross_purchase_amount" type="number" min="0" required /></label></div></template>

    <template v-else-if="formKind === 'asset-verification'"><h2>New asset verification</h2><div class="form-grid"><label class="full-field">Asset<select v-model="form.asset" required><option value="" disabled>Select asset</option><option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name }} — {{ a.name }}</option></select></label><label>Verification date<input v-model="form.verification_date" type="date" required /></label><label>Condition<select v-model="form.condition"><option>Good</option><option>Fair</option><option>Damaged</option><option>Missing</option></select></label><label class="full-field">Remarks<textarea v-model="form.remarks"></textarea></label></div></template>

    <template v-else-if="formKind === 'asset-movement'"><h2>{{ form.purpose }} asset</h2><div class="form-grid"><label class="full-field">Asset<select v-model="form.asset" required><option value="" disabled>Select asset</option><option v-for="a in assets" :key="a.name" :value="a.name">{{ a.asset_name }} — {{ a.name }}</option></select></label><label>Transaction date<input v-model="form.transaction_date" type="date" required /></label><label>Target location<select v-model="form.target_location"><option value="">No change</option><option v-for="loc in options.locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option></select></label><label>To employee<select v-model="form.to_employee"><option value="">No change</option><option v-for="e in options.employees" :key="e.name" :value="e.name">{{ e.employee_name }}</option></select></label><label>Source location<select v-model="form.source_location"><option value="">No change</option><option v-for="loc in options.locations" :key="loc.name" :value="loc.name">{{ loc.name }}</option></select></label><label>From employee<select v-model="form.from_employee"><option value="">No change</option><option v-for="e in options.employees" :key="e.name" :value="e.name">{{ e.employee_name }}</option></select></label></div></template>

    <template v-else-if="formKind === 'vehicle'"><h2>New vehicle</h2><div class="form-grid"><label>License plate<input v-model="form.license_plate" required /></label><label>Make<input v-model="form.make" required /></label><label>Model<input v-model="form.model" required /></label><label>Last odometer<input v-model.number="form.last_odometer" type="number" min="0" required /></label><label>Fuel type<select v-model="form.fuel_type"><option>Petrol</option><option>Diesel</option><option>Natural Gas</option><option>Electric</option></select></label><label>Fuel UOM<input v-model="form.uom" placeholder="Nos" required /></label><label>Insurance company<input v-model="form.insurance_company" /></label><label>Policy end date<input v-model="form.end_date" type="date" /></label></div></template>

    <template v-else-if="formKind === 'vehicle-log'"><h2>New fuel / trip record</h2><div class="form-grid"><label class="full-field">Vehicle<select v-model="form.license_plate" required><option value="" disabled>Select vehicle</option><option v-for="v in vehicles" :key="v.name" :value="v.name">{{ v.name }} — {{ v.make }} {{ v.model }}</option></select></label><label>Date<input v-model="form.date" type="date" required /></label><label>Odometer<input v-model.number="form.odometer" type="number" min="0" required /></label><label>Fuel qty<input v-model.number="form.fuel_qty" type="number" min="0" step="0.01" /></label><label>Fuel price<input v-model.number="form.price" type="number" min="0" step="0.01" /></label></div></template>

    <p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save record" }}</button></footer>
  </form></div>
</template>
