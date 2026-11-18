import { z } from "zod";

const row = z.object({ label: z.string(), value: z.number() });
const lgaRow = row.extend({ company: z.string(), verified: z.number() });

export const workforceSummarySchema = z.object({
  scope: z.object({ companies: z.number(), is_statewide: z.boolean() }),
  totals: z.object({
    total: z.number(),
    active: z.number(),
    left: z.number(),
    verified: z.number(),
    pending_verification: z.number(),
    retiring_12m: z.number(),
    past_retirement: z.number(),
    joined_this_year: z.number(),
    average_age: z.number().nullable(),
  }),
  breakdowns: z.object({
    lga: z.array(lgaRow),
    status: z.array(row),
    gender: z.array(row),
    grade_level: z.array(row),
    verification: z.array(row),
    age_band: z.array(row),
    department: z.array(row),
    retirements_by_year: z.array(row),
    appointments_by_year: z.array(row),
  }),
});

export type WorkforceSummary = z.infer<typeof workforceSummarySchema>;
export type BreakdownRow = z.infer<typeof row>;

export function percent(part: number, whole: number) {
  return whole ? Math.round((part / whole) * 100) : 0;
}
