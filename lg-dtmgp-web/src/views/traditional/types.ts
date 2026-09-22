export interface Dashboard { active_institutions: number; reigning_rulers: number; vacant_stools: number; pending_recognition: number; open_petitions: number; can_manage: boolean }
export interface FormOptions { institutions: { name: string; institution_name: string }[]; ruling_houses: { name: string; house_name: string; institution: string }[]; rulers: { name: string; ruler_name: string }[] }
export interface Institution { name: string; institution_name: string; institution_type: string; rank_class: string | null; parent_institution: string | null; seat_location: string | null; status: string; founding_basis?: string; history?: string }
export interface Ruler { name: string; ruler_name: string; institution: string; ruling_house: string | null; appointment_date: string; installation_date: string | null; status: string; reign_end_date: string | null }
export interface RulingHouse { name: string; house_name: string; institution: string; rotation_order: number; is_eligible: number; last_occupied_from: string | null }
export interface Appointment { name: string; institution: string; candidate_name: string; ruling_house: string | null; application_date: string; status: string; gazette_reference: string | null; gazette_date: string | null; installation_date: string | null; recognition_status: string }
export interface SuccessionCase { name: string; institution: string; vacancy_date: string; vacancy_reason: string; status: string; eligible_ruling_house: string | null; candidates: string | null; selected_candidate: string | null; resulting_appointment: string | null }
export interface Petition { name: string; institution: string; respondent_institution: string | null; petitioner_name: string; petition_type: string; petition_date: string; status: string; hearing_date: string | null; decision: string | null; decision_date: string | null }
export interface Allowance { name: string; ruler: string; allowance_type: string; amount: number; period_start: string; period_end: string; status: string; payment_date: string | null }
export interface ReportGroup { label: string; count: number }
export interface Reports { institutions_by_type: ReportGroup[]; rulers_by_status: ReportGroup[]; appointments_by_stage: ReportGroup[]; succession_by_status: ReportGroup[]; petitions_by_status: ReportGroup[] }

export const APPOINTMENT_CHAIN = ["Nominated", "Kingmakers Selection", "Council Endorsed", "Ministry Vetting", "Exco Approved", "Governor Approved", "Gazetted", "Installed"] as const;
export const SUCCESSION_CHAIN = ["Open", "Candidates Nominated", "Kingmakers Deliberation", "Selected", "Closed"] as const;
export const PETITION_CHAIN = ["Filed", "Council Hearing", "Panel of Inquiry", "Exco Review", "Decided", "Appealed", "Closed"] as const;
export const ALLOWANCE_CHAIN = ["Draft", "Approved", "Paid"] as const;

export function nextInChain(chain: readonly string[], status: string): string | null {
  const index = chain.indexOf(status);
  return index >= 0 && index < chain.length - 1 ? chain[index + 1] : null;
}
export function today() { return new Date().toISOString().slice(0, 10); }
export function money(value: unknown) { return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(Number(value || 0)); }
