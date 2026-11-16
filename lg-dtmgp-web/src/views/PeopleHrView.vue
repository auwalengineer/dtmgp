<script setup lang="ts">
import { BadgeCheck, CalendarDays, CircleAlert, UserPlus, UsersRound } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import AttendanceSection from "./hr/AttendanceSection.vue";
import EstablishmentSection from "./hr/EstablishmentSection.vue";
import LeaveSection from "./hr/LeaveSection.vue";
import PayrollSection from "./hr/PayrollSection.vue";
import PostingTransfersSection from "./hr/PostingTransfersSection.vue";
import PromotionsSection from "./hr/PromotionsSection.vue";
import ReportsSection from "./hr/ReportsSection.vue";
import RetirementExitSection from "./hr/RetirementExitSection.vue";
import StaffAuditSection from "./hr/StaffAuditSection.vue";
import StaffSection from "./hr/StaffSection.vue";
import type { AttendanceItem, AttendanceSummary, AuditExceptions, Dashboard, Department, Employee, Exercise, HRReports, Leave, LeaveBalance, Options, PayrollOverview, Position, Promotion, RetirementItem, Separation, StaffingPlan, Transfer, VerificationRecord } from "./hr/types";
import VerificationSection from "./hr/VerificationSection.vue";

const TAB_LABELS = ["Staff directory", "Verification", "Establishment", "Postings & Transfers", "Promotions", "Leave", "Attendance", "Exit & Retirement", "Payroll", "Staff Audit", "Reports"] as const;
type Tab = typeof TAB_LABELS[number];
const SECTION_TAB: Record<string, Tab> = { staff: "Staff directory", "verification-biometrics": "Verification", "establishment-control": "Establishment", "posting-transfers": "Postings & Transfers", promotions: "Promotions", leave: "Leave", attendance: "Attendance", "retirement-exit": "Exit & Retirement", payroll: "Payroll", "staff-audit": "Staff Audit", "hr-reports": "Reports" };

const session = useSessionStore();
const route = useRoute();
const visibleTabs = computed(() => TAB_LABELS.filter((tab) => (tab !== "Payroll" || session.canViewPayroll) && (tab !== "Staff Audit" || session.canViewStaffAudit)));
const activeTab = ref<Tab>(SECTION_TAB[String(route.params.section || "")] || "Staff directory");
const dashboard = ref<Dashboard | null>(null);
const employees = ref<Employee[]>([]);
const options = ref<Options>({ departments: [], designations: [], genders: [], statuses: [], verification_statuses: [] });
const lgaOptions = ref<string[]>([]);
const leave = ref<Leave[]>([]);
const leaveBalances = ref<LeaveBalance[]>([]);
const departments = ref<Department[]>([]);
const staffingPlans = ref<StaffingPlan[]>([]);
const positions = ref<Position[]>([]);
const transfers = ref<Transfer[]>([]);
const promotions = ref<Promotion[]>([]);
const exercises = ref<Exercise[]>([]);
const activeExercise = ref("");
const verificationRecords = ref<VerificationRecord[]>([]);
const retirementForecast = ref<RetirementItem[]>([]);
const separations = ref<Separation[]>([]);
const separationDetail = ref<Separation | null>(null);
const attendanceSummary = ref<AttendanceSummary | null>(null);
const attendanceItems = ref<AttendanceItem[]>([]);
const payroll = ref<PayrollOverview | null>(null);
const auditExceptions = ref<AuditExceptions | null>(null);
const hrReports = ref<HRReports | null>(null);
const search = ref("");
const department = ref("");
const page = ref(1);
const total = ref(0);
const pageSize = 25;
const loading = ref(true);
const error = ref("");
const showEmployeeForm = ref(false);
const editingEmployee = ref<string | null>(null);
const employeeForm = ref(emptyEmployeeForm());
const showForm = ref(false);
const formKind = ref<"plan" | "transfer" | "promotion" | "exercise" | "record" | "separation">("plan");
const form = ref<Record<string, string | number>>({});
const saving = ref(false);

function emptyEmployeeForm() {
  return { first_name: "", last_name: "", company: session.activeLga, gender: "", date_of_birth: "", date_of_joining: "", department: "", designation: "", grade_level: "", status: "Active", verification_status: "Pending" };
}
function scopeQuery() { return `company=${encodeURIComponent(session.activeLga)}`; }
function shortLga() { return session.activeLga.replace(" Local Government Area", " LGA"); }
function today() { return new Date().toISOString().slice(0, 10); }

async function loadModule() {
  loading.value = true;
  error.value = "";
  page.value = 1;
  try {
    const [summary, formOptions, lgas] = await Promise.all([
      apiRequest<Dashboard>(`/api/method/dtmgp.api.v1.people.get_dashboard?${scopeQuery()}`),
      apiRequest<Options>(`/api/method/dtmgp.api.v1.people.get_form_options?${scopeQuery()}`),
      apiRequest<string[]>("/api/method/dtmgp.api.v1.hr.list_lga_companies"),
    ]);
    dashboard.value = summary;
    options.value = formOptions;
    lgaOptions.value = lgas;
    await loadEmployees();
    await selectTab(activeTab.value);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load People and HR";
  } finally {
    loading.value = false;
  }
}

async function loadEmployees() {
  const params = new URLSearchParams({ company: session.activeLga, page: String(page.value), page_size: String(pageSize) });
  if (search.value.trim()) params.set("search", search.value.trim());
  if (department.value) params.set("department", department.value);
  const result = await apiRequest<{ items: Employee[]; total: number }>(`/api/method/dtmgp.api.v1.people.list_employees?${params}`);
  employees.value = result.items;
  total.value = result.total;
}

async function selectTab(tab: Tab) {
  activeTab.value = tab;
  if (tab === "Staff directory") await loadEmployees();
  else if (tab === "Establishment") await loadEstablishment();
  else if (tab === "Verification") await loadVerification();
  else if (tab === "Postings & Transfers") await loadTransfers();
  else if (tab === "Promotions") await loadPromotions();
  else if (tab === "Leave") { await loadLeave(); leaveBalances.value = await apiRequest<LeaveBalance[]>(`/api/method/dtmgp.api.v1.hr.get_leave_balances?${scopeQuery()}`); }
  else if (tab === "Attendance") await loadAttendance();
  else if (tab === "Exit & Retirement") await loadExit();
  else if (tab === "Payroll") payroll.value = await apiRequest<PayrollOverview>(`/api/method/dtmgp.api.v1.hr.get_payroll_overview?${scopeQuery()}`);
  else if (tab === "Staff Audit") auditExceptions.value = await apiRequest<AuditExceptions>(`/api/method/dtmgp.api.v1.hr.get_staff_audit_exceptions?${scopeQuery()}`);
  else if (tab === "Reports") hrReports.value = await apiRequest<HRReports>(`/api/method/dtmgp.api.v1.hr.get_hr_reports?${scopeQuery()}`);
}
watch(() => route.params.section, (section) => { const mapped = SECTION_TAB[String(section || "")]; if (mapped) selectTab(mapped); });

async function loadEstablishment() {
  departments.value = await apiRequest<Department[]>(`/api/method/dtmgp.api.v1.people.get_establishment?${scopeQuery()}`);
  staffingPlans.value = (await apiRequest<{ items: StaffingPlan[] }>(`/api/method/dtmgp.api.v1.hr.list_staffing_plans?${scopeQuery()}`)).items;
  const report = await apiRequest<{ positions: Position[] }>(`/api/method/dtmgp.api.v1.hr.get_establishment_report?${scopeQuery()}`);
  positions.value = report.positions;
}
async function loadTransfers() { transfers.value = (await apiRequest<{ items: Transfer[] }>(`/api/method/dtmgp.api.v1.hr.list_employee_transfers?${scopeQuery()}`)).items; }
async function loadPromotions() { promotions.value = (await apiRequest<{ items: Promotion[] }>(`/api/method/dtmgp.api.v1.hr.list_employee_promotions?${scopeQuery()}`)).items; }
async function loadVerification() {
  exercises.value = (await apiRequest<{ items: Exercise[] }>(`/api/method/dtmgp.api.v1.hr.list_verification_exercises?${scopeQuery()}`)).items;
  if (!activeExercise.value && exercises.value.length) activeExercise.value = exercises.value[0].name;
  await loadVerificationRecords();
}
async function loadVerificationRecords() {
  const params = new URLSearchParams({ company: session.activeLga });
  if (activeExercise.value) params.set("exercise", activeExercise.value);
  verificationRecords.value = (await apiRequest<{ items: VerificationRecord[] }>(`/api/method/dtmgp.api.v1.hr.list_verification_records?${params}`)).items;
}
function selectExercise(name: string) { activeExercise.value = name; loadVerificationRecords(); }
async function loadLeave() { leave.value = await apiRequest<Leave[]>(`/api/method/dtmgp.api.v1.people.list_leave?${scopeQuery()}`); }
async function loadAttendance() {
  attendanceSummary.value = await apiRequest<AttendanceSummary>(`/api/method/dtmgp.api.v1.hr.get_attendance_summary?${scopeQuery()}`);
  attendanceItems.value = (await apiRequest<{ items: AttendanceItem[] }>(`/api/method/dtmgp.api.v1.hr.list_attendance?${scopeQuery()}&attendance_date=${today()}`)).items;
}
async function loadExit() {
  retirementForecast.value = await apiRequest<RetirementItem[]>(`/api/method/dtmgp.api.v1.hr.get_retirement_forecast?${scopeQuery()}&months=12`);
  separations.value = (await apiRequest<{ items: Separation[] }>(`/api/method/dtmgp.api.v1.hr.list_employee_separations?${scopeQuery()}`)).items;
}

async function applyFilters() { page.value = 1; await loadEmployees(); }
async function changePage(change: number) { page.value += change; await loadEmployees(); }

function openCreateEmployee() { editingEmployee.value = null; employeeForm.value = emptyEmployeeForm(); showEmployeeForm.value = true; }
function openEditEmployee(employee: Employee) {
  editingEmployee.value = employee.name;
  employeeForm.value = { first_name: employee.first_name, last_name: employee.last_name || "", company: employee.company, gender: employee.gender, date_of_birth: employee.date_of_birth, date_of_joining: employee.date_of_joining, department: employee.department || "", designation: employee.designation || "", grade_level: employee.dtmgp_grade_level || "", status: employee.status, verification_status: employee.dtmgp_verification_status || "Pending" };
  showEmployeeForm.value = true;
}
async function saveEmployee() {
  saving.value = true;
  error.value = "";
  try {
    await apiRequest("/api/method/dtmgp.api.v1.people.save_employee", { method: "POST", body: JSON.stringify({ ...employeeForm.value, employee: editingEmployee.value }) });
    showEmployeeForm.value = false;
    await loadModule();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to save employee";
  } finally { saving.value = false; }
}

function openForm(kind: typeof formKind.value, initial: Record<string, string | number>) { formKind.value = kind; form.value = initial; showForm.value = true; }
async function saveForm() {
  saving.value = true;
  error.value = "";
  const endpoint: Record<typeof formKind.value, string> = { plan: "save_staffing_plan", transfer: "save_employee_transfer", promotion: "save_employee_promotion", exercise: "save_verification_exercise", record: "save_verification_record", separation: "save_employee_separation" };
  try {
    const payload: Record<string, unknown> = { ...form.value };
    if (formKind.value === "plan") {
      payload.company = session.activeLga;
      payload.staffing_details = [{ designation: form.value.designation, vacancies: form.value.vacancies }];
      delete payload.designation;
      delete payload.vacancies;
    }
    await apiRequest(`/api/method/dtmgp.api.v1.hr.${endpoint[formKind.value]}`, { method: "POST", body: JSON.stringify({ values: payload }) });
    showForm.value = false;
    await selectTab(activeTab.value);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to save record";
  } finally { saving.value = false; }
}

async function submitStaffingPlan(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.submit_staffing_plan", { method: "POST", body: JSON.stringify({ name }) }); await loadEstablishment(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to approve the staffing plan"; } }
async function submitTransfer(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.submit_employee_transfer", { method: "POST", body: JSON.stringify({ name }) }); await loadTransfers(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to submit the posting or transfer"; } }
async function cancelTransfer(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.cancel_employee_transfer", { method: "POST", body: JSON.stringify({ name }) }); await loadTransfers(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to cancel the posting or transfer"; } }
async function submitPromotion(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.submit_employee_promotion", { method: "POST", body: JSON.stringify({ name }) }); await loadPromotions(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to approve the promotion review"; } }
async function transitionExercise(name: string, target: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.transition_verification_exercise", { method: "POST", body: JSON.stringify({ name, target_status: target }) }); await loadVerification(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to update the exercise"; } }
async function reviewRecord(name: string, status: "Verified" | "Exception") { error.value = ""; try { const exception_reason = status === "Exception" ? window.prompt("Exception reason") || "" : undefined; await apiRequest("/api/method/dtmgp.api.v1.hr.review_verification_record", { method: "POST", body: JSON.stringify({ name, review_status: status, exception_reason }) }); await loadVerificationRecords(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to review the record"; } }
async function decideLeave(name: string, decision: "Approved" | "Rejected") { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.decide_leave_application", { method: "POST", body: JSON.stringify({ name, decision }) }); await loadLeave(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to decide the leave application"; } }
async function submitSeparation(name: string) { error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.submit_employee_separation", { method: "POST", body: JSON.stringify({ name }) }); await loadExit(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to submit the exit case"; } }
async function openSeparationDetail(name: string) { separationDetail.value = await apiRequest<Separation>(`/api/method/dtmgp.api.v1.hr.get_employee_separation?name=${encodeURIComponent(name)}`); }
async function completeActivity(activityName: string) { if (!separationDetail.value) return; error.value = ""; try { await apiRequest("/api/method/dtmgp.api.v1.hr.complete_separation_activity", { method: "POST", body: JSON.stringify({ name: separationDetail.value.name, activity_name: activityName }) }); await openSeparationDetail(separationDetail.value.name); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to complete the activity"; } }

watch(() => session.activeLga, loadModule, { immediate: true });
</script>

<template>
  <section class="hr-heading">
    <div><p class="eyebrow">{{ shortLga() }}</p><h1>People & HR</h1><p>Workforce records, verification, establishment, movements and payroll</p></div>
    <button v-if="dashboard?.can_manage && activeTab === 'Staff directory'" class="primary-action" @click="openCreateEmployee"><UserPlus :size="17" /> Add employee</button>
  </section>
  <p v-if="error" class="login-error" role="alert">{{ error }}</p>
  <section v-if="loading" class="panel loading-panel">Loading workforce records...</section>
  <template v-else-if="dashboard">
    <section class="hr-metrics" aria-label="Workforce summary">
      <article><span class="hr-metric-icon green"><UsersRound :size="19" /></span><div><small>Total staff</small><strong>{{ dashboard.total }}</strong><p>{{ dashboard.active }} active</p></div></article>
      <article><span class="hr-metric-icon blue"><BadgeCheck :size="19" /></span><div><small>Verified records</small><strong>{{ dashboard.verified }}</strong><p>{{ dashboard.total ? Math.round(dashboard.verified / dashboard.total * 100) : 0 }}% complete</p></div></article>
      <article><span class="hr-metric-icon gold"><CalendarDays :size="19" /></span><div><small>On leave</small><strong>{{ dashboard.on_leave }}</strong><p>Approved leave today</p></div></article>
      <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Needs attention</small><strong>{{ dashboard.needs_attention }}</strong><p>Records to verify</p></div></article>
    </section>

    <section class="hr-workspace">
      <nav class="hr-tabs" aria-label="People and HR views"><button v-for="tab in visibleTabs" :key="tab" :class="{ active: activeTab === tab }" @click="selectTab(tab)">{{ tab }}</button></nav>

      <StaffSection v-if="activeTab === 'Staff directory'" :employees="employees" :total="total" :page="page" :page-size="pageSize" v-model:search="search" v-model:department="department" :department-options="options.departments" :can-manage="dashboard.can_manage" @apply-filters="applyFilters" @change-page="changePage" @edit-employee="openEditEmployee" @photo-changed="loadEmployees" />

      <VerificationSection v-else-if="activeTab === 'Verification'" :exercises="exercises" :active-exercise="activeExercise" :verification-records="verificationRecords" :can-manage="dashboard.can_manage" @new-exercise="openForm('exercise', { company: session.activeLga, title: '', cycle_start_date: today(), cycle_end_date: today() })" @select-exercise="selectExercise" @transition-exercise="transitionExercise" @new-record="openForm('record', { company: session.activeLga, exercise: activeExercise, employee: '', biometric_captured: 0 })" @review-record="reviewRecord" />

      <EstablishmentSection v-else-if="activeTab === 'Establishment'" :staffing-plans="staffingPlans" :positions="positions" :departments="departments" :can-manage="dashboard.can_manage" @new-staffing-plan="openForm('plan', { department: '', from_date: today(), to_date: today(), designation: '', vacancies: 1 })" @submit-staffing-plan="submitStaffingPlan" />

      <PostingTransfersSection v-else-if="activeTab === 'Postings & Transfers'" :transfers="transfers" :can-manage="dashboard.can_manage" @new-movement="openForm('transfer', { employee: '', transfer_date: today(), movement_type: 'Posting', to_department: '', new_company: '' })" @submit-transfer="submitTransfer" @cancel-transfer="cancelTransfer" />

      <PromotionsSection v-else-if="activeTab === 'Promotions'" :promotions="promotions" :can-manage="dashboard.can_manage" @new-review="openForm('promotion', { employee: '', promotion_date: today(), proposed_grade_level: '' })" @submit-promotion="submitPromotion" />

      <LeaveSection v-else-if="activeTab === 'Leave'" :leave="leave" :leave-balances="leaveBalances" :can-manage="dashboard.can_manage" @decide-leave="decideLeave" />

      <AttendanceSection v-else-if="activeTab === 'Attendance'" :attendance-summary="attendanceSummary" :attendance-items="attendanceItems" />

      <RetirementExitSection v-else-if="activeTab === 'Exit & Retirement'" :retirement-forecast="retirementForecast" :separations="separations" :can-manage="dashboard.can_manage" @new-exit-case="openForm('separation', { employee: '', resignation_letter_date: today() })" @submit-separation="submitSeparation" @open-separation-detail="openSeparationDetail" />

      <PayrollSection v-else-if="activeTab === 'Payroll' && payroll" :payroll="payroll" />

      <StaffAuditSection v-else-if="activeTab === 'Staff Audit' && auditExceptions" :audit-exceptions="auditExceptions" />

      <ReportsSection v-else-if="activeTab === 'Reports' && hrReports" :hr-reports="hrReports" />
    </section>
  </template>

  <div v-if="showEmployeeForm" class="modal-backdrop" @click.self="showEmployeeForm = false"><form class="user-modal employee-modal" @submit.prevent="saveEmployee"><h2>{{ editingEmployee ? "Edit employee" : "Add employee" }}</h2><div class="form-grid"><label>First name<input v-model="employeeForm.first_name" required /></label><label>Last name<input v-model="employeeForm.last_name" /></label><label>Gender<select v-model="employeeForm.gender" required><option value="" disabled>Select gender</option><option v-for="item in options.genders" :key="item">{{ item }}</option></select></label><label>Date of birth<input v-model="employeeForm.date_of_birth" type="date" required /></label><label>Date joined<input v-model="employeeForm.date_of_joining" type="date" required /></label><label>Department<select v-model="employeeForm.department"><option value="">Unassigned</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Designation<select v-model="employeeForm.designation"><option value="">Unassigned</option><option v-for="item in options.designations" :key="item">{{ item }}</option></select></label><label>Grade level<input v-model="employeeForm.grade_level" placeholder="GL 08" /></label><label>Employment status<select v-model="employeeForm.status"><option v-for="item in options.statuses" :key="item">{{ item }}</option></select></label></div><p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showEmployeeForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save employee" }}</button></footer></form></div>

  <div v-if="showForm" class="modal-backdrop" @click.self="showForm = false"><form class="user-modal" @submit.prevent="saveForm">
    <template v-if="formKind === 'plan'"><h2>New staffing plan</h2><div class="form-grid"><label>Department<select v-model="form.department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label>Designation<select v-model="form.designation" required><option value="" disabled>Select designation</option><option v-for="item in options.designations" :key="item">{{ item }}</option></select></label><label>From date<input v-model="form.from_date" type="date" required /></label><label>To date<input v-model="form.to_date" type="date" required /></label><label>Vacancies<input v-model.number="form.vacancies" type="number" min="0" required /></label></div></template>
    <template v-else-if="formKind === 'transfer'"><h2>New posting or transfer</h2><div class="form-grid"><label>Movement type<select v-model="form.movement_type"><option>Posting</option><option>Transfer</option></select></label><label>Employee<select v-model="form.employee" required><option value="" disabled>Select employee</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }}</option></select></label><label v-if="form.movement_type === 'Posting'">To department<select v-model="form.to_department" required><option value="" disabled>Select department</option><option v-for="item in options.departments" :key="item">{{ item }}</option></select></label><label v-else>Destination LGA<select v-model="form.new_company" required><option value="" disabled>Select LGA</option><option v-for="item in lgaOptions" :key="item" :value="item">{{ item.replace(' Local Government Area', ' LGA') }}</option></select></label><label>Effective date<input v-model="form.transfer_date" type="date" required /></label></div></template>
    <template v-else-if="formKind === 'promotion'"><h2>New promotion review</h2><div class="form-grid"><label>Employee<select v-model="form.employee" required><option value="" disabled>Select employee</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }}</option></select></label><label>Proposed grade level<input v-model="form.proposed_grade_level" placeholder="GL 10" required /></label><label>Review date<input v-model="form.promotion_date" type="date" required /></label></div></template>
    <template v-else-if="formKind === 'exercise'"><h2>New verification exercise</h2><div class="form-grid"><label class="full-field">Title<input v-model="form.title" required /></label><label>Cycle start<input v-model="form.cycle_start_date" type="date" required /></label><label>Cycle end<input v-model="form.cycle_end_date" type="date" required /></label></div></template>
    <template v-else-if="formKind === 'record'"><h2>Prepare verification record</h2><div class="form-grid"><label>Employee<select v-model="form.employee" required><option value="" disabled>Select employee</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }}</option></select></label><label>Biometric captured<select v-model="form.biometric_captured"><option :value="0">Not yet</option><option :value="1">Captured</option></select></label></div></template>
    <template v-else-if="formKind === 'separation'"><h2>New exit case</h2><div class="form-grid"><label>Employee<select v-model="form.employee" required><option value="" disabled>Select employee</option><option v-for="item in employees" :key="item.name" :value="item.name">{{ item.employee_name }}</option></select></label><label>Resignation letter date<input v-model="form.resignation_letter_date" type="date" required /></label><label class="full-field">Exit interview notes<textarea v-model="form.exit_interview"></textarea></label></div></template>
    <p v-if="error" class="login-error" role="alert">{{ error }}</p><footer><button type="button" class="secondary-action" @click="showForm = false">Cancel</button><button class="primary-action" :disabled="saving">{{ saving ? "Saving..." : "Save" }}</button></footer>
  </form></div>

  <div v-if="separationDetail" class="modal-backdrop" @click.self="separationDetail = null"><div class="user-modal"><h2>Clearance checklist</h2><p>{{ separationDetail.employee_name }} · {{ separationDetail.boarding_status }}</p>
    <ul style="list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:10px">
      <li v-for="activity in separationDetail.activities" :key="activity.activity_name" style="display:flex;align-items:center;justify-content:space-between;gap:10px"><span>{{ activity.activity_name }}<small v-if="activity.role"> · {{ activity.role }}</small></span><span v-if="activity.status === 'Completed'" class="table-status success">Completed</span><button v-else class="secondary-action compact-action" @click="completeActivity(activity.activity_name)">Complete</button></li>
    </ul>
    <footer><button type="button" class="secondary-action" @click="separationDetail = null">Close</button></footer>
  </div></div>
</template>
