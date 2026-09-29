export interface Dashboard {
  scope: string;
  lga_count: number;
  projects: { total: number; ongoing: number; completed: number; delayed: number; suspended: number; abandoned: number };
  inspections: { open: number; exceptions: number };
  assets: { registered: number };
  fleet: { vehicles: number; insurance_due: number };
  can_manage: boolean;
}

export interface Options {
  employees: { name: string; employee_name: string }[];
  locations: { name: string; latitude: number | null; longitude: number | null }[];
  asset_categories: string[];
  items: { name: string; item_name: string }[];
  open_projects: { name: string; project_name: string }[];
  vehicle_service_items: string[];
}

export interface Project {
  name: string;
  project_name: string;
  company: string;
  status: string;
  percent_complete: number;
  expected_start_date: string | null;
  expected_end_date: string | null;
  dtmgp_location: string | null;
  dtmgp_funding_source: string | null;
  department: string | null;
  priority: string;
  creation: string;
}

export interface Task {
  name: string;
  project: string;
  subject: string;
  is_milestone: number;
  status: string;
  priority: string;
  exp_start_date: string | null;
  exp_end_date: string | null;
  progress: number;
}

export interface AssetRecord { name: string; company: string; asset_name: string; asset_category: string; location: string | null; custodian: string | null; status: string; purchase_date: string; gross_purchase_amount: number; docstatus: number }
export interface AssetMovementRecord { name: string; company: string; purpose: string; transaction_date: string; docstatus: number }
export interface AssetMaintenanceRecord { name: string; company: string; asset_name: string; maintenance_team: string | null }
export interface VehicleRecord { name: string; company: string; make: string; model: string; last_odometer: number; location: string | null; employee: string | null; insurance_company: string | null; policy_no: string | null; end_date: string | null }
export interface VehicleLogRecord { name: string; license_plate: string; employee: string | null; date: string; odometer: number; fuel_qty: number; price: number; supplier: string | null; invoice: string | null; docstatus: number }
export interface InspectionRecord { name: string; company: string; project: string; scheduled_date: string; inspector: string | null; status: string; latitude: number | null; longitude: number | null; findings: string | null; recommendation?: string | null; exception_reason?: string | null; photo_evidence?: string | null }
export interface AssetVerificationRecord { name: string; company: string; asset: string; verification_date: string; verified_by: string | null; condition: string; remarks?: string | null }
export interface Contractor { name: string; supplier_name: string; supplier_type: string; supplier_group: string | null; disabled: number; on_hold: number; hold_type: string | null }
export interface ContractorPerformance { supplier: string; cases: number; completed: number; estimated_total: number; evaluated_total: number }

export interface ReportsData {
  project_status: { total: number; ongoing: number; completed: number; delayed: number; suspended: number; abandoned: number };
  project_performance: { average_percent_complete: number; delayed: number };
  inspections: Record<string, number>;
  assets: Record<string, number>;
  fleet: { vehicle_count: number; total_fuel_cost: number };
}

export interface GeoPoint { name: string; latitude: number; longitude: number;[key: string]: unknown }
export interface MapsData { projects: GeoPoint[]; assets: GeoPoint[]; inspections: GeoPoint[] }

export type ProjectView = "ongoing" | "completed" | "delayed" | "suspended" | "abandoned";

export function projectView(project: Pick<Project, "status" | "expected_end_date">): ProjectView {
  if (project.status === "Completed") return "completed";
  if (project.status === "Cancelled") return "abandoned";
  if (project.status === "On hold") return "suspended";
  if (project.expected_end_date && project.expected_end_date < today()) return "delayed";
  return "ongoing";
}

export function isNewProject(project: Pick<Project, "creation">) { return project.creation >= new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(); }
export function today() { return new Date().toISOString().slice(0, 10); }
export function mapLink(latitude: number, longitude: number) { return `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=16/${latitude}/${longitude}`; }
