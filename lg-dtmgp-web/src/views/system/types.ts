export interface PlatformRole { role: string; desk_access: number; user_count: number }
export interface RoleProfile { name: string; roles: string[] }
export interface LgaAccessUser { name: string; full_name: string; enabled: number; roles: string[] }
export interface LgaAccessRow { company: string; users: LgaAccessUser[] }
export interface UserSession { user: string; sid: string | null; ipaddress: string | null; lastupdate: string; status: string }
export interface LgaProfile { name: string; lga_name: string; lga_code: string; company: string; enabled: number }
export interface DepartmentItem { name: string; department_name: string; company: string; disabled: number; is_group: number; parent_department: string | null }
export interface Designation { name: string; designation_name: string; description: string | null }
export interface FiscalYearRow { name: string; year: string; year_start_date: string; year_end_date: string; disabled: number }
export interface LocationRow { name: string; location_name: string; parent_location: string | null; is_group: number; latitude: number | null; longitude: number | null }
export interface ApprovalDelegation { name: string; company: string; delegator: string; delegate: string; role: string; start_date: string; end_date: string; active: number }
export interface DocumentNumberingEntry { doctype: string; autoname: string }
export interface AuditEvent { name: string; occurred_at: string; event_type: string; outcome: string; actor: string; company: string | null; reference_doctype: string | null; reference_name: string | null; summary: string; metadata: Record<string, unknown>; ip_address: string | null }
export interface LoginHistoryRow { name: string; user: string; full_name: string; operation: string; status: string; creation: string; ip_address: string | null }
