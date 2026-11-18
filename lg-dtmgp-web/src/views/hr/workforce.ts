import { z } from "zod";

const row = z.object({ label: z.string(), value: z.number(), count: z.number().optional() });
const lgaRow = row.extend({ company: z.string(), verified: z.number() });
const nullableNumber = z.number().nullable();

export const comparisonRowSchema = z.object({
  company: z.string(),
  label: z.string(),
  total: z.number(),
  active: z.number(),
  left: z.number(),
  verified: z.number(),
  pending_verification: z.number(),
  retiring_12m: z.number(),
  past_retirement: z.number(),
  joined_this_year: z.number(),
  average_age: nullableNumber,
  average_service: nullableNumber,
  male: z.number(),
  female: z.number(),
  share_pct: z.number(),
  verified_pct: z.number(),
  female_pct: z.number(),
  management_pct: z.number(),
  bvn_pct: z.number(),
  nin_pct: z.number(),
  photo_pct: z.number(),
  bank_pct: z.number(),
  phone_pct: z.number(),
  first_appointment_pct: z.number(),
  grade_bands: z.record(z.number()),
});

export const comparisonMetricSchema = z.object({ key: z.string(), label: z.string(), unit: z.enum(["count", "pct", "years"]) });

export const workforceSummarySchema = z.object({
  scope: z.object({ companies: z.number(), is_statewide: z.boolean() }),
  totals: z.object({
    total: z.number(),
    active: z.number(),
    left: z.number(),
    suspended_or_inactive: z.number(),
    verified: z.number(),
    pending_verification: z.number(),
    male: z.number(),
    female: z.number(),
    retiring_12m: z.number(),
    retiring_5y: z.number(),
    past_retirement: z.number(),
    joined_this_year: z.number(),
    average_age: nullableNumber,
    average_service: nullableNumber,
    completeness: z.record(z.number()),
  }),
  breakdowns: z.object({
    lga: z.array(lgaRow),
    status: z.array(row),
    gender: z.array(row),
    grade_level: z.array(row),
    grade_band: z.array(row),
    verification: z.array(row),
    age_band: z.array(row),
    service_band: z.array(row),
    department: z.array(row),
    designation: z.array(row),
    rank: z.array(row),
    salary_mode: z.array(row),
    data_completeness: z.array(row),
    retirements_by_year: z.array(row),
    appointments_by_year: z.array(row),
  }),
  lga_comparison: z.array(comparisonRowSchema),
  comparison_metrics: z.array(comparisonMetricSchema),
});

export type WorkforceSummary = z.infer<typeof workforceSummarySchema>;
export type BreakdownRow = z.infer<typeof row>;
export type ComparisonRow = z.infer<typeof comparisonRowSchema>;
export type ComparisonMetric = z.infer<typeof comparisonMetricSchema>;
export type MetricKey = keyof Omit<ComparisonRow, "company" | "label" | "grade_bands">;

export function percent(part: number, whole: number) {
  return whole ? Math.round((part / whole) * 100) : 0;
}

export function formatMetric(value: number | null | undefined, unit: ComparisonMetric["unit"]) {
  if (value === null || value === undefined) return "—";
  if (unit === "pct") return `${Number.isInteger(value) ? value : value.toFixed(1)}%`;
  if (unit === "years") return value.toFixed(1);
  return value.toLocaleString();
}

/** Headcount-weighted state average for a per-LGA metric (counts are summed instead). */
export function scopeAverage(rows: ComparisonRow[], key: MetricKey, unit: ComparisonMetric["unit"]) {
  if (unit === "count") {
    const withStaff = rows.filter((row) => row.active);
    return withStaff.length ? withStaff.reduce((sum, row) => sum + Number(row[key] ?? 0), 0) / withStaff.length : null;
  }
  const weighted = rows.filter((row) => row.active && row[key] !== null);
  const weight = weighted.reduce((sum, row) => sum + row.active, 0);
  return weight ? weighted.reduce((sum, row) => sum + Number(row[key]) * row.active, 0) / weight : null;
}
