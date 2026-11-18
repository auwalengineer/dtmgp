import { z } from "zod";

/** Server-built HR reports (dtmgp.hr_reports). The UI renders them generically. */
const cell = z.union([z.string(), z.number(), z.boolean(), z.null()]);
export const reportColumnSchema = z.object({ key: z.string(), label: z.string(), type: z.enum(["text", "int", "pct", "years", "date"]) });
export const hrReportSchema = z.object({
  columns: z.array(reportColumnSchema),
  rows: z.array(z.record(z.string(), cell)),
  totals: z.record(z.string(), cell).nullable(),
  summary: z.array(z.object({ label: z.string(), value: z.union([z.string(), z.number()]), unit: z.string().optional(), tone: z.string().optional() })),
  note: z.string().nullable(),
  truncated: z.boolean(),
});
const option = z.object({ value: z.string(), label: z.string() });
export const hrReportOptionsSchema = z.object({
  departments: z.array(option),
  statuses: z.array(z.string()),
  group_by: z.array(option),
  dimensions: z.array(option),
  leave_groups: z.array(option),
  retirement_horizons: z.array(z.number()),
  is_statewide: z.boolean(),
});

export type ReportColumn = z.infer<typeof reportColumnSchema>;
export type HrReport = z.infer<typeof hrReportSchema>;
export type HrReportOptions = z.infer<typeof hrReportOptionsSchema>;
export type ReportFilter = "department" | "status" | "group_by" | "dimension" | "leave_group" | "months" | "period";

export interface ReportDefinition { id: string; report: string; label: string; description: string; filters: ReportFilter[]; listing?: boolean }

/** Keyed by the navigation item slug (dtmgp/navigation.py, "HR Reports"). */
export const HR_REPORTS: ReportDefinition[] = [
  { id: "nominal-roll", report: "nominal-roll", label: "Nominal Roll", description: "Named list of staff with grade, step, rank and key service dates.", filters: ["status", "department"], listing: true },
  { id: "staff-strength-report", report: "staff-strength", label: "Staff Strength Report", description: "Headcount by unit with gender, cadre and employment status.", filters: ["group_by", "department"] },
  { id: "staff-distribution-report", report: "staff-distribution", label: "Staff Distribution Report", description: "How active staff spread across one dimension, with gender split.", filters: ["dimension", "department"] },
  { id: "retirement-forecast", report: "retirement-forecast", label: "Retirement Forecast", description: "Named staff due to retire, and active staff already past retirement.", filters: ["months", "department"], listing: true },
  { id: "appointments-exits", report: "appointments-exits", label: "Appointments & Exits", description: "Appointments, exits and inter-LGA transfers in a period.", filters: ["period", "department"], listing: true },
  { id: "leave-report", report: "leave", label: "Leave Report", description: "Leave applications, decisions and days approved in a period.", filters: ["leave_group", "period", "department"] },
  { id: "establishment-report", report: "establishment", label: "Establishment Report", description: "Approved positions against filled posts from submitted staffing plans.", filters: ["department"] },
  { id: "verification-report", report: "verification", label: "Verification Report", description: "Verification status of active staff, lowest rate first.", filters: ["group_by", "department"] },
  { id: "records-completeness", report: "records-completeness", label: "Records Completeness", description: "Share of active staff with each key record captured.", filters: ["group_by", "department"] },
];

const DATE = new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" });

export function formatCell(value: unknown, type: ReportColumn["type"]) {
  if (value === null || value === undefined || value === "") return "—";
  if (type === "date" && typeof value === "string") { const date = new Date(`${value}T00:00:00`); return Number.isNaN(date.getTime()) ? value : DATE.format(date); }
  if (typeof value !== "number") return String(value);
  if (type === "pct") return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
  if (type === "years") return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(1);
  return value.toLocaleString();
}

export function isNumeric(type: ReportColumn["type"]) { return type === "int" || type === "pct" || type === "years"; }

export function compareCells(a: unknown, b: unknown) {
  if (a === b) return 0;
  if (a === null || a === undefined || a === "") return 1;
  if (b === null || b === undefined || b === "") return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, { numeric: true });
}

export function startOfYear(today = new Date()) { return `${today.getFullYear()}-01-01`; }
export function isoDate(date = new Date()) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
