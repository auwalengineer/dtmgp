export interface Dashboard { total: number; active: number; verified: number; on_leave: number; needs_attention: number; can_manage: boolean }
export interface Employee { name: string; employee_name: string; first_name: string; last_name: string; company: string; department: string | null; designation: string | null; status: string; date_of_joining: string; date_of_birth: string; gender: string; image?: string | null; dtmgp_grade_level: string; dtmgp_verification_status: string }
export interface Options { departments: string[]; designations: string[]; genders: string[]; statuses: string[]; verification_statuses: string[] }
export interface Leave { name: string; employee: string; employee_name: string; leave_type: string; from_date: string; to_date: string; total_leave_days: number; status: string }
export interface Department { name: string; department_name: string; company: string; employee_count: number }
export interface StaffingPlan { name: string; company: string; department: string | null; from_date: string; to_date: string; docstatus: number; total_estimated_budget: number }
export interface Position { parent: string; designation: string; number_of_positions: number; current_count: number; current_openings: number; vacancies: number; position_status: string }
export interface Transfer { name: string; employee: string; employee_name: string; company: string; new_company: string | null; department: string | null; transfer_date: string; docstatus: number; owner: string; movement_type: string }
export interface Promotion { name: string; employee: string; employee_name: string; company: string; promotion_date: string; docstatus: number; owner: string }
export interface Exercise { name: string; company: string; title: string; cycle_start_date: string; cycle_end_date: string; status: string }
export interface VerificationRecord { name: string; company: string; exercise: string; employee: string; prepared_by: string; biometric_captured: number; review_status: string; reviewed_by: string | null; exception_reason: string | null }
export interface SeparationActivity { activity_name: string; role: string | null; task: string | null; status: string }
export interface Separation { name: string; employee: string; employee_name: string; company?: string; boarding_status: string; resignation_letter_date: string | null; docstatus: number; dtmgp_exit_type?: string; activities?: SeparationActivity[] }
export interface RetirementItem { name: string; employee_name: string; company: string; department: string | null; designation: string | null; date_of_retirement: string }
export interface AttendanceItem { name: string; employee: string; employee_name: string; attendance_date: string; status: string; late_entry: number; early_exit: number }
export interface AttendanceSummary { date: string; present: number; absent: number; on_leave: number; half_day: number; late_entries: number }
export interface LeaveBalance { employee: string; employee_name: string; leave_type: string; total_leaves_allocated: number; taken: number; balance: number }
export interface PayrollOverview { draft: number; submitted: number; paid: number }
export interface AuditExceptions { unverified: Employee[]; duplicate_candidates: { employee_name: string; date_of_birth: string; employees: string[] }[]; missing_grade: Employee[] }
export interface HRReports { strength_by_department: { department: string; count: number }[]; distribution_by_gender: { gender: string; count: number }[]; retirement_forecast_12m: number; leave_by_type: { leave_type: string; days: number }[]; establishment: { approved_total: number; filled_total: number; vacant_count: number } }

export function docstatusLabel(docstatus: number, submittedLabel = "Submitted") { return docstatus === 1 ? submittedLabel : (docstatus === 2 ? "Cancelled" : "Draft"); }
export function initials(name: string) { return name.split(" ").filter(Boolean).map(part => part[0]).slice(0, 2).join(""); }
