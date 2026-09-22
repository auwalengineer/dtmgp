<script setup lang="ts">
import { Building2, CalendarCheck, ClipboardCheck, FilePlus2, FileText, Gavel, Inbox, Landmark, Mail, ScrollText, Search, Send, ShieldCheck, UserCheck, X } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

interface Dashboard {
  scope: string; can_manage: boolean;
  correspondence: { draft: number; registered: number; dispatched: number; overdue_assigned: number };
  departments: number; meetings_scheduled: number; resolutions_proposed: number;
  actions_overdue: number; returns_overdue: number; compliance_non_compliant: number; pending_approvals: number;
}
interface Reports {
  meetings: { scheduled: number; held: number; cancelled: number; postponed: number };
  resolutions: { proposed: number; adopted: number; rejected: number };
  resolution_actions: { pending: number; completed: number; overdue: number };
  statutory_returns: { submitted: number; overdue: number };
  compliance: { verified: number; non_compliant: number; pending: number };
}
interface Row { name: string; [key: string]: unknown }
interface DepartmentItem { name: string; department_name: string; company: string; disabled: number; is_group: number; parent_department: string | null }
interface ApprovalItem { doctype: string; name: string; title: string; company: string; status: string }
interface RefItem { name: string; return_name?: string; requirement_name?: string; frequency: string }
interface Options {
  departments: string[]; users: { name: string; full_name: string }[]; meetings: { name: string; title: string }[];
  resolutions: { name: string; title: string }[]; return_types: RefItem[]; compliance_requirements: RefItem[]; roles: string[];
}
interface ItemFilter { label: string; correspondence_type?: string; status?: string; assignedToMe?: boolean; overdue?: boolean }
interface TableMeta { doctype: string; columns: [string, string][]; next: Record<string, string[]> }

const NEXT_STATUS: Record<string, string[]> = { Draft: ["Registered"], Registered: ["Dispatched", "Closed"], Dispatched: ["Closed"], Closed: [] };
const MEETING_NEXT: Record<string, string[]> = { Scheduled: ["Held", "Postponed", "Cancelled"], Postponed: ["Scheduled"], Held: [], Cancelled: [] };
const RESOLUTION_NEXT: Record<string, string[]> = { Proposed: ["Adopted", "Rejected"], Adopted: ["Rescinded"], Rejected: [], Rescinded: [] };
const ACTION_NEXT: Record<string, string[]> = { Pending: ["In Progress", "Completed"], "In Progress": ["Completed"], Completed: [] };
const RETURN_NEXT: Record<string, string[]> = { Draft: ["Prepared"], Prepared: ["Submitted"], Submitted: ["State Reviewed", "Returned"], Returned: ["Prepared"], "State Reviewed": [] };
const COMPLIANCE_NEXT: Record<string, string[]> = { Pending: ["Submitted"], Submitted: ["Verified", "Non-Compliant"], Verified: [], "Non-Compliant": [] };

const TABLE_META: Record<string, TableMeta> = {
  correspondence: { doctype: "DTMGP Correspondence", columns: [["correspondence_type", "Type"], ["subject", "Subject"], ["correspondent", "From / To"], ["correspondence_date", "Date"], ["status", "Status"]], next: NEXT_STATUS },
  meetings: { doctype: "DTMGP Meeting", columns: [["meeting_type", "Type"], ["title", "Title"], ["meeting_date", "Date"], ["venue", "Venue"], ["status", "Status"]], next: MEETING_NEXT },
  resolutions: { doctype: "DTMGP Resolution", columns: [["title", "Title"], ["meeting", "Meeting"], ["category", "Category"], ["status", "Status"]], next: RESOLUTION_NEXT },
  actions: { doctype: "DTMGP Resolution Action", columns: [["action_description", "Action"], ["resolution", "Resolution"], ["assigned_to", "Assigned To"], ["due_date", "Due"], ["status", "Status"]], next: ACTION_NEXT },
  returns: { doctype: "DTMGP Statutory Return", columns: [["return_type", "Return Type"], ["period", "Period"], ["due_date", "Due"], ["status", "Status"]], next: RETURN_NEXT },
  compliance: { doctype: "DTMGP Compliance Submission", columns: [["requirement", "Requirement"], ["period", "Period"], ["due_date", "Due"], ["status", "Status"]], next: COMPLIANCE_NEXT },
  delegations: { doctype: "DTMGP Approval Delegation", columns: [["delegator", "Delegator"], ["delegate", "Delegate"], ["role", "Delegated Role"], ["end_date", "Until"], ["active", "Active"]], next: {} },
};
const TABS = [
  { key: "correspondence", label: "Correspondence" },
  { key: "meetings", label: "Meetings" },
  { key: "resolutions", label: "Resolutions" },
  { key: "returns", label: "Statutory Returns" },
  { key: "compliance", label: "Compliance" },
  { key: "approvals", label: "Approvals" },
  { key: "departments", label: "Departments & Units" },
  { key: "reports", label: "Reports" },
];
// Correspondence's own sub-links filter the same list rather than being separate pages.
const ITEM_FILTERS: Record<string, ItemFilter> = {
  "incoming-correspondence": { label: "Incoming Correspondence", correspondence_type: "Incoming" },
  "outgoing-correspondence": { label: "Outgoing Correspondence", correspondence_type: "Outgoing" },
  "internal-memos": { label: "Internal Memos", correspondence_type: "Internal Memo" },
  "dispatch-register": { label: "Dispatch Register", status: "Dispatched" },
  "assigned-correspondence": { label: "Assigned Correspondence", assignedToMe: true },
  "overdue-actions": { label: "Overdue Actions", overdue: true },
  "overdue-returns": { label: "Overdue Returns", overdue: true },
};

const route = useRoute();
const router = useRouter();
const session = useSessionStore();
const active = ref(TABS[0]);
const dashboard = ref<Dashboard | null>(null);
const reports = ref<Reports | null>(null);
const options = ref<Options>({ departments: [], users: [], meetings: [], resolutions: [], return_types: [], compliance_requirements: [], roles: [] });
const records = ref<Row[]>([]);
const departments = ref<DepartmentItem[]>([]);
const approvalsInbox = ref<ApprovalItem[]>([]);
const total = ref(0);
const search = ref("");
const loading = ref(true);
const error = ref("");
const showForm = ref(false);
const saving = ref(false);
const today = () => new Date().toISOString().slice(0, 10);

const sectionId = computed(() => String(route.params.section || ""));
const itemId = computed(() => String(route.params.item || ""));
const itemFilter = computed(() => ITEM_FILTERS[itemId.value]);

// Driven by the locally-clickable `active` tab (synchronous — a tab click must not
// wait on an async route round-trip to change what's rendered), refined by the
// route's `itemId` for deep-linked sub-items. `active` itself is kept in sync with
// the route by the `sectionId` watcher below, so the two never disagree in practice.
const mode = computed(() => {
  const key = active.value.key;
  if (key === "resolutions" && ["assigned-actions", "action-progress", "overdue-actions"].includes(itemId.value)) return "actions";
  if (key === "returns" && itemId.value === "return-requirements") return "return-types";
  if (key === "compliance" && itemId.value === "compliance-requirements") return "compliance-requirements";
  if (key === "compliance" && itemId.value === "compliance-scorecard") return "reports";
  if (key === "approvals" && itemId.value === "delegated-approvals") return "delegations";
  if (key === "approvals" && (itemId.value === "approved-requests" || itemId.value === "rejected-requests")) return "resolutions";
  if (key === "approvals") return "approvals-inbox";
  if (key === "reports") return "reports";
  if (["meetings", "resolutions", "returns", "compliance", "departments"].includes(key)) return key;
  return "correspondence";
});
const tableMeta = computed(() => TABLE_META[mode.value]);
const isTableMode = computed(() => !!tableMeta.value);

function titleCase(slug: string) { return slug.split("-").map((part) => part[0].toUpperCase() + part.slice(1)).join(" "); }
const navItem = computed(() => {
  const module = session.navigation.find((entry) => entry.id === "governance");
  const section = module?.children.find((entry) => entry.id === sectionId.value);
  const item = section?.children?.find((entry) => entry.id === itemId.value);
  const fallback = sectionId.value ? titleCase(sectionId.value) : "Administration & Governance";
  return { title: item?.label || section?.label || fallback };
});
const createLabel = computed(() => ({
  correspondence: "correspondence", meetings: "meeting", resolutions: "resolution", actions: "action",
  returns: "statutory return", compliance: "compliance submission", delegations: "delegation", departments: "department",
} as Record<string, string>)[mode.value] || "record");

const correspondenceForm = ref(emptyCorrespondenceForm());
const departmentForm = ref(emptyDepartmentForm());
const meetingForm = ref(emptyMeetingForm());
const resolutionForm = ref(emptyResolutionForm());
const actionForm = ref(emptyActionForm());
const returnForm = ref(emptyReturnForm());
const complianceForm = ref(emptyComplianceForm());
const delegationForm = ref(emptyDelegationForm());

function emptyCorrespondenceForm() {
  return { company: session.activeLga, correspondence_type: itemFilter.value?.correspondence_type || "Incoming", subject: "", correspondent: "", department: "", correspondence_date: today(), priority: "Routine", assigned_to: "", due_date: "", summary: "" };
}
function emptyDepartmentForm() { return { company: session.activeLga, department_name: "", parent_department: "" }; }
function emptyMeetingForm() { return { company: session.activeLga, meeting_type: "Council", title: "", meeting_date: today(), venue: "", chairperson: "", convened_by: "", agendaText: "", attendeesText: "", minutes: "" }; }
function emptyResolutionForm() { return { company: session.activeLga, meeting: "", title: "", category: "Administrative", resolution_text: "" }; }
function emptyActionForm() { return { company: session.activeLga, resolution: "", action_description: "", responsible_department: "", assigned_to: "", due_date: today(), remarks: "" }; }
function emptyReturnForm() { return { company: session.activeLga, return_type: "", period: "", due_date: today() }; }
function emptyComplianceForm() { return { company: session.activeLga, requirement: "", period: "", due_date: today() }; }
function emptyDelegationForm() { return { company: session.activeLga, delegator: "", delegate: "", role: "", start_date: today(), end_date: today(), active: 1 }; }

async function loadModule() {
  if (!session.activeLga) return;
  loading.value = true;
  error.value = "";
  try {
    const company = encodeURIComponent(session.activeLga);
    [dashboard.value, options.value] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.governance.get_dashboard?company=${company}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.governance.get_form_options?company=${company}`),
    ]);
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to load governance workspace"; }
  finally { loading.value = false; }
}
async function loadRecords() {
  if (mode.value === "departments") {
    departments.value = await apiRequest<DepartmentItem[]>(`/api/method/dtmgp.api.v1.governance.list_departments?company=${encodeURIComponent(session.activeLga)}`);
    total.value = departments.value.length;
    return;
  }
  if (mode.value === "reports") {
    reports.value = await apiRequest<Reports>(`/api/method/dtmgp.api.v1.governance.get_reports?company=${encodeURIComponent(session.activeLga)}`);
    return;
  }
  if (mode.value === "approvals-inbox") {
    approvalsInbox.value = await apiRequest<ApprovalItem[]>(`/api/method/dtmgp.api.v1.governance.get_approvals_inbox?company=${encodeURIComponent(session.activeLga)}`);
    total.value = approvalsInbox.value.length;
    return;
  }
  if (mode.value === "return-types" || mode.value === "compliance-requirements") {
    total.value = mode.value === "return-types" ? options.value.return_types.length : options.value.compliance_requirements.length;
    return;
  }
  const meta = tableMeta.value;
  if (!meta) return;
  const params = new URLSearchParams({ doctype: meta.doctype, company: session.activeLga });
  if (search.value.trim()) params.set("search", search.value.trim());
  const filter = itemFilter.value;
  if (filter?.correspondence_type) params.set("correspondence_type", filter.correspondence_type);
  if (filter?.status) params.set("status", filter.status);
  if (filter?.assignedToMe) params.set("assigned_to", session.user.email);
  if (itemId.value === "approved-requests") params.set("status", "Adopted");
  if (itemId.value === "rejected-requests") params.set("status", "Rejected");
  const result = await apiRequest<{ items: Row[]; total: number }>(`/api/method/dtmgp.api.v1.governance.list_records?${params}`);
  // "Overdue" sub-items have no dedicated server filter (governance module has no
  // generic before-date param yet); approximated client-side against the fetched page.
  records.value = filter?.overdue ? result.items.filter((item) => item.status !== "Completed" && item.status !== "Submitted" && item.status !== "State Reviewed" && typeof item.due_date === "string" && item.due_date < today()) : result.items;
  total.value = filter?.overdue ? records.value.length : result.total;
}
const TAB_TO_SECTION: Record<string, string> = { correspondence: "correspondence", meetings: "meetings", resolutions: "resolutions", returns: "statutory-returns", compliance: "compliance", approvals: "approvals", departments: "departments-units", reports: "reports" };
async function chooseTab(tab: typeof TABS[number]) {
  // `active` drives `mode` synchronously so the click is reflected immediately;
  // the route push just keeps the URL shareable/bookmarkable and runs in the
  // background rather than gating the UI update on navigation completing.
  active.value = tab; search.value = "";
  if (sectionId.value !== TAB_TO_SECTION[tab.key]) router.push(`/workspace/governance/${TAB_TO_SECTION[tab.key]}`);
  await loadRecords();
}
function clearFilter() { router.push(`/workspace/governance/${TAB_TO_SECTION[active.value.key]}`); }
function openCreate() {
  correspondenceForm.value = emptyCorrespondenceForm();
  departmentForm.value = emptyDepartmentForm();
  meetingForm.value = emptyMeetingForm();
  resolutionForm.value = { ...emptyResolutionForm(), meeting: options.value.meetings[0]?.name || "" };
  actionForm.value = { ...emptyActionForm(), resolution: options.value.resolutions[0]?.name || "" };
  returnForm.value = { ...emptyReturnForm(), return_type: options.value.return_types[0]?.name || "" };
  complianceForm.value = { ...emptyComplianceForm(), requirement: options.value.compliance_requirements[0]?.name || "" };
  delegationForm.value = emptyDelegationForm();
  showForm.value = true;
}
async function save(doctype: string, values: Record<string, unknown>) {
  saving.value = true; error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.save_record", { method: "POST", body: JSON.stringify({ doctype, values }) });
    showForm.value = false; await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save record"; }
  finally { saving.value = false; }
}
function saveCorrespondence() { return save("DTMGP Correspondence", correspondenceForm.value); }
function saveMeeting() {
  const { agendaText, attendeesText, ...rest } = meetingForm.value;
  const agenda_items = agendaText.split("\n").map((line) => line.trim()).filter(Boolean).map((agenda_item) => ({ agenda_item }));
  const attendees = attendeesText.split("\n").map((line) => line.trim()).filter(Boolean).map((attendee_name) => ({ attendee_name }));
  return save("DTMGP Meeting", { ...rest, agenda_items, attendees });
}
function saveResolution() { return save("DTMGP Resolution", resolutionForm.value); }
function saveAction() { return save("DTMGP Resolution Action", actionForm.value); }
function saveReturn() { return save("DTMGP Statutory Return", returnForm.value); }
function saveCompliance() { return save("DTMGP Compliance Submission", complianceForm.value); }
function saveDelegation() { return save("DTMGP Approval Delegation", delegationForm.value); }
async function saveDepartment() {
  saving.value = true; error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.save_department", { method: "POST", body: JSON.stringify({ values: departmentForm.value }) });
    showForm.value = false; await loadModule();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to save department"; }
  finally { saving.value = false; }
}
async function transition(item: Row, targetStatus: string) {
  const meta = tableMeta.value;
  if (!meta) return;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.transition_record", { method: "POST", body: JSON.stringify({ doctype: meta.doctype, name: item.name, target_status: targetStatus }) });
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update status"; }
}
async function actOnApproval(item: ApprovalItem, targetStatus: string) {
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.governance.transition_record", { method: "POST", body: JSON.stringify({ doctype: item.doctype, name: item.name, target_status: targetStatus }) });
    await loadRecords();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to act on this item"; }
}

watch(() => session.activeLga, loadModule, { immediate: true });
watch(sectionId, async (value) => {
  const found = TABS.find((tab) => tab.key === value || (value === "statutory-returns" && tab.key === "returns") || (value === "departments-units" && tab.key === "departments"));
  active.value = found || TABS[0];
  if (session.activeLga) await loadRecords();
}, { immediate: true });
watch(itemId, async () => { if (session.activeLga) await loadRecords(); });
</script>

<template>
  <section class="hr-heading"><div><p class="eyebrow">{{ dashboard?.scope || session.activeLga }}</p><h1>{{ navItem.title }}</h1><p>Governance, meetings, resolutions, statutory compliance and approvals for the LGA secretariat</p></div><button v-if="dashboard?.can_manage && !['reports', 'approvals-inbox', 'return-types', 'compliance-requirements'].includes(mode)" class="primary-action" @click="openCreate"><FilePlus2 :size="17" /> New {{ createLabel }}</button></section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading governance records...</section>

  <template v-else-if="dashboard">
    <section class="finance-metrics" aria-label="Governance summary">
      <article><span class="hr-metric-icon blue"><Inbox :size="19" /></span><div><small>Draft correspondence</small><strong>{{ dashboard.correspondence.draft }}</strong><p>{{ dashboard.correspondence.registered }} registered</p></div></article>
      <article><span class="hr-metric-icon green"><CalendarCheck :size="19" /></span><div><small>Meetings scheduled</small><strong>{{ dashboard.meetings_scheduled }}</strong><p>{{ dashboard.resolutions_proposed }} resolutions proposed</p></div></article>
      <article><span class="hr-metric-icon gold"><ScrollText :size="19" /></span><div><small>Returns overdue</small><strong>{{ dashboard.returns_overdue }}</strong><p>{{ dashboard.actions_overdue }} actions overdue</p></div></article>
      <article><span class="hr-metric-icon red"><ShieldCheck :size="19" /></span><div><small>Pending approvals</small><strong>{{ dashboard.pending_approvals }}</strong><p>{{ dashboard.compliance_non_compliant }} non-compliant</p></div></article>
    </section>
    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="Governance views"><button v-for="tab in TABS" :key="tab.key" :class="{ active: active.key === tab.key }" @click="chooseTab(tab)">{{ tab.label }}</button></nav>
      <form v-if="isTableMode" class="directory-toolbar" @submit.prevent="loadRecords"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search" /></label><button class="secondary-action">Search</button><span v-if="itemFilter" class="status-badge">{{ itemFilter.label }}</span><button v-if="itemFilter" type="button" class="secondary-action" @click="clearFilter"><X :size="14" /> Clear</button></form>

      <div v-if="isTableMode" class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Reference</th><th v-for="column in tableMeta!.columns" :key="column[0]">{{ column[1] }}</th><th>Action</th></tr></thead>
          <tbody>
            <tr v-for="item in records" :key="item.name">
              <td><strong>{{ item.name }}</strong></td>
              <td v-for="column in tableMeta!.columns" :key="column[0]"><span v-if="column[0] === 'status'" class="table-status" :class="['Closed', 'Held', 'Adopted', 'Completed', 'Submitted', 'State Reviewed', 'Verified'].includes(String(item[column[0]])) ? 'success' : 'neutral'">{{ item[column[0]] }}</span><template v-else>{{ item[column[0]] === 1 ? 'Yes' : item[column[0]] === 0 ? 'No' : (item[column[0]] || '-') }}</template></td>
              <td><button v-for="next in (tableMeta!.next[String(item.status)] || [])" :key="next" class="secondary-action" type="button" @click="transition(item, next)">{{ next }}</button></td>
            </tr>
          </tbody>
        </table>
        <p v-if="!records.length" class="users-empty">No {{ itemFilter ? itemFilter.label.toLowerCase() : navItem.title.toLowerCase() }} in this LGA.</p>
        <footer class="table-footer"><span>{{ total }} records</span><span>Scoped to {{ session.activeLga }}</span></footer>
      </div>

      <div v-else-if="mode === 'departments'" class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Department</th><th>Parent</th><th>Status</th></tr></thead>
          <tbody>
            <tr v-for="item in departments" :key="item.name">
              <td><strong>{{ item.department_name }}</strong></td>
              <td>{{ item.parent_department || '-' }}</td>
              <td><span class="table-status" :class="item.disabled ? 'neutral' : 'success'">{{ item.disabled ? 'Disabled' : 'Active' }}</span></td>
            </tr>
          </tbody>
        </table>
        <p v-if="!departments.length" class="users-empty">No departments or units registered in this LGA.</p>
        <footer class="table-footer"><span>{{ total }} departments</span><span>Scoped to {{ session.activeLga }}</span></footer>
      </div>

      <div v-else-if="mode === 'approvals-inbox'" class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Reference</th><th>Type</th><th>Title / Period</th><th>Status</th><th>Action</th></tr></thead>
          <tbody>
            <tr v-for="item in approvalsInbox" :key="item.doctype + item.name">
              <td><strong>{{ item.name }}</strong></td>
              <td>{{ item.doctype.replace('DTMGP ', '') }}</td>
              <td>{{ item.title }}</td>
              <td><span class="table-status neutral">{{ item.status }}</span></td>
              <td>
                <button v-if="item.doctype === 'DTMGP Resolution'" class="secondary-action" type="button" @click="actOnApproval(item, 'Adopted')">Adopt</button>
                <button v-if="item.doctype === 'DTMGP Resolution'" class="secondary-action" type="button" @click="actOnApproval(item, 'Rejected')">Reject</button>
                <button v-if="item.doctype === 'DTMGP Statutory Return'" class="secondary-action" type="button" @click="actOnApproval(item, 'State Reviewed')">State Review</button>
                <button v-if="item.doctype === 'DTMGP Statutory Return'" class="secondary-action" type="button" @click="actOnApproval(item, 'Returned')">Return</button>
                <button v-if="item.doctype === 'DTMGP Compliance Submission'" class="secondary-action" type="button" @click="actOnApproval(item, 'Verified')">Verify</button>
                <button v-if="item.doctype === 'DTMGP Compliance Submission'" class="secondary-action" type="button" @click="actOnApproval(item, 'Non-Compliant')">Non-Compliant</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!approvalsInbox.length" class="users-empty">Nothing is awaiting your approval in this LGA.</p>
        <footer class="table-footer"><span>{{ total }} pending</span><span>Scoped to {{ session.activeLga }}</span></footer>
      </div>

      <div v-else-if="mode === 'return-types' || mode === 'compliance-requirements'" class="staff-table-wrap">
        <table class="staff-table finance-table">
          <thead><tr><th>Name</th><th>Frequency</th></tr></thead>
          <tbody>
            <tr v-for="item in (mode === 'return-types' ? options.return_types : options.compliance_requirements)" :key="item.name">
              <td><strong>{{ item.return_name || item.requirement_name }}</strong></td>
              <td>{{ item.frequency }}</td>
            </tr>
          </tbody>
        </table>
        <p class="users-empty">State-managed reference catalogue — a starter set pending full business confirmation (see docs/implementation-status.md).</p>
      </div>

      <div v-else-if="mode === 'reports' && reports" class="finance-metrics" aria-label="Governance reports">
        <article><span class="hr-metric-icon blue"><Landmark :size="19" /></span><div><small>Meetings</small><strong>{{ reports.meetings.held }} held</strong><p>{{ reports.meetings.scheduled }} scheduled &middot; {{ reports.meetings.postponed }} postponed &middot; {{ reports.meetings.cancelled }} cancelled</p></div></article>
        <article><span class="hr-metric-icon green"><Gavel :size="19" /></span><div><small>Resolutions</small><strong>{{ reports.resolutions.adopted }} adopted</strong><p>{{ reports.resolutions.proposed }} proposed &middot; {{ reports.resolutions.rejected }} rejected</p></div></article>
        <article><span class="hr-metric-icon gold"><UserCheck :size="19" /></span><div><small>Resolution actions</small><strong>{{ reports.resolution_actions.completed }} completed</strong><p>{{ reports.resolution_actions.pending }} pending &middot; {{ reports.resolution_actions.overdue }} overdue</p></div></article>
        <article><span class="hr-metric-icon red"><FileText :size="19" /></span><div><small>Statutory returns</small><strong>{{ reports.statutory_returns.submitted }} submitted</strong><p>{{ reports.statutory_returns.overdue }} overdue</p></div></article>
        <article><span class="hr-metric-icon green"><ShieldCheck :size="19" /></span><div><small>Compliance</small><strong>{{ reports.compliance.verified }} verified</strong><p>{{ reports.compliance.pending }} pending &middot; {{ reports.compliance.non_compliant }} non-compliant</p></div></article>
      </div>
    </section>
  </template>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false">
    <form v-if="mode === 'correspondence'" class="user-modal finance-modal" @submit.prevent="saveCorrespondence">
      <h2>New correspondence</h2>
      <div class="form-grid">
        <label>Type<select v-model="correspondenceForm.correspondence_type"><option>Incoming</option><option>Outgoing</option><option>Internal Memo</option></select></label>
        <label>Priority<select v-model="correspondenceForm.priority"><option>Routine</option><option>Urgent</option><option>Confidential</option></select></label>
        <label class="full-field">Subject<input v-model="correspondenceForm.subject" required /></label>
        <label>Sender / recipient<input v-model="correspondenceForm.correspondent" /></label>
        <label>Department<select v-model="correspondenceForm.department"><option value="">Unassigned</option><option v-for="item in options.departments" :key="item" :value="item">{{ item }}</option></select></label>
        <label>Date<input v-model="correspondenceForm.correspondence_date" type="date" required /></label>
        <label>Due date<input v-model="correspondenceForm.due_date" type="date" /></label>
        <label>Assigned to<select v-model="correspondenceForm.assigned_to"><option value="">Unassigned</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label class="full-field">Summary<textarea v-model="correspondenceForm.summary"></textarea></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save correspondence' }}</button></footer>
    </form>

    <form v-else-if="mode === 'meetings'" class="user-modal finance-modal" @submit.prevent="saveMeeting">
      <h2>New meeting</h2>
      <div class="form-grid">
        <label>Type<select v-model="meetingForm.meeting_type"><option>Council</option><option>Committee</option></select></label>
        <label class="full-field">Title<input v-model="meetingForm.title" required /></label>
        <label>Date<input v-model="meetingForm.meeting_date" type="date" required /></label>
        <label>Venue<input v-model="meetingForm.venue" /></label>
        <label>Chairperson<input v-model="meetingForm.chairperson" /></label>
        <label>Convened by<select v-model="meetingForm.convened_by"><option value="">Unassigned</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label class="full-field">Agenda (one item per line)<textarea v-model="meetingForm.agendaText"></textarea></label>
        <label class="full-field">Attendees (one name per line)<textarea v-model="meetingForm.attendeesText"></textarea></label>
        <label class="full-field">Minutes<textarea v-model="meetingForm.minutes"></textarea></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save meeting' }}</button></footer>
    </form>

    <form v-else-if="mode === 'resolutions'" class="user-modal finance-modal" @submit.prevent="saveResolution">
      <h2>New resolution</h2>
      <div class="form-grid">
        <label>Meeting<select v-model="resolutionForm.meeting" required><option value="" disabled>Select meeting</option><option v-for="item in options.meetings" :key="item.name" :value="item.name">{{ item.title }}</option></select></label>
        <label>Category<select v-model="resolutionForm.category"><option>Policy</option><option>Financial</option><option>Administrative</option><option>Other</option></select></label>
        <label class="full-field">Title<input v-model="resolutionForm.title" required /></label>
        <label class="full-field">Resolution text<textarea v-model="resolutionForm.resolution_text" required></textarea></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save resolution' }}</button></footer>
    </form>

    <form v-else-if="mode === 'actions'" class="user-modal finance-modal" @submit.prevent="saveAction">
      <h2>New resolution action</h2>
      <div class="form-grid">
        <label>Resolution<select v-model="actionForm.resolution" required><option value="" disabled>Select resolution</option><option v-for="item in options.resolutions" :key="item.name" :value="item.name">{{ item.title }}</option></select></label>
        <label>Responsible department<select v-model="actionForm.responsible_department"><option value="">Unassigned</option><option v-for="item in options.departments" :key="item" :value="item">{{ item }}</option></select></label>
        <label>Assigned to<select v-model="actionForm.assigned_to"><option value="">Unassigned</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label>Due date<input v-model="actionForm.due_date" type="date" required /></label>
        <label class="full-field">Action<textarea v-model="actionForm.action_description" required></textarea></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save action' }}</button></footer>
    </form>

    <form v-else-if="mode === 'returns'" class="user-modal finance-modal" @submit.prevent="saveReturn">
      <h2>New statutory return</h2>
      <div class="form-grid">
        <label>Return type<select v-model="returnForm.return_type" required><option value="" disabled>Select return type</option><option v-for="item in options.return_types" :key="item.name" :value="item.name">{{ item.return_name }}</option></select></label>
        <label>Period<input v-model="returnForm.period" placeholder="e.g. 2026-Q3" required /></label>
        <label>Due date<input v-model="returnForm.due_date" type="date" required /></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save return' }}</button></footer>
    </form>

    <form v-else-if="mode === 'compliance'" class="user-modal finance-modal" @submit.prevent="saveCompliance">
      <h2>New compliance submission</h2>
      <div class="form-grid">
        <label>Requirement<select v-model="complianceForm.requirement" required><option value="" disabled>Select requirement</option><option v-for="item in options.compliance_requirements" :key="item.name" :value="item.name">{{ item.requirement_name }}</option></select></label>
        <label>Period<input v-model="complianceForm.period" placeholder="e.g. 2026-Q3" required /></label>
        <label>Due date<input v-model="complianceForm.due_date" type="date" required /></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save submission' }}</button></footer>
    </form>

    <form v-else-if="mode === 'delegations'" class="user-modal finance-modal" @submit.prevent="saveDelegation">
      <h2>New approval delegation</h2>
      <div class="form-grid">
        <label>Delegator<select v-model="delegationForm.delegator" required><option value="" disabled>Select delegator</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label>Delegate<select v-model="delegationForm.delegate" required><option value="" disabled>Select delegate</option><option v-for="user in options.users" :key="user.name" :value="user.name">{{ user.full_name }}</option></select></label>
        <label>Delegated role<select v-model="delegationForm.role" required><option value="" disabled>Select role</option><option v-for="role in options.roles" :key="role" :value="role">{{ role }}</option></select></label>
        <label>From<input v-model="delegationForm.start_date" type="date" required /></label>
        <label>Until<input v-model="delegationForm.end_date" type="date" required /></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save delegation' }}</button></footer>
    </form>

    <form v-else class="user-modal finance-modal" @submit.prevent="saveDepartment">
      <h2>New department / unit</h2>
      <div class="form-grid">
        <label class="full-field">Name<input v-model="departmentForm.department_name" required /></label>
        <label>Parent department<select v-model="departmentForm.parent_department"><option value="">None</option><option v-for="item in options.departments" :key="item" :value="item">{{ item }}</option></select></label>
      </div>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? 'Saving...' : 'Save department' }}</button></footer>
    </form>
  </div>
</template>
