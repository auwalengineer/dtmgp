export interface Dashboard { scope: string; lga_count: number; revenue: { assessed: number; collected: number; outstanding: number }; procurement: { planned: number; active: number; pending_approval: number }; payments: { pending: number; paid: number }; audit: { open_queries: number; overdue_queries: number }; can_manage: boolean }
export interface Options { departments: string[]; accounts: string[]; cost_centers: string[]; fiscal_years: string[]; revenue_heads: { name: string; revenue_name: string }[]; procurement_plans: { name: string; title: string }[] }
export interface RevenueHead { name: string; company: string; revenue_code: string; revenue_name: string; rate_type: string; default_rate: number; disabled: number }
export interface RevenueAssessment { name: string; company: string; revenue_head: string; taxpayer_name: string; assessment_date: string; due_date: string; amount: number; amount_paid: number; status: string }
export interface RevenueReceipt { name: string; company: string; assessment: string; posting_date: string; amount: number; payment_channel: string; bank_reference: string; docstatus: number }
export interface ProcurementPlan { name: string; company: string; fiscal_year: string; title: string; procurement_category: string; procurement_method: string; estimated_amount: number; status: string }
export interface ProcurementCase { name: string; company: string; title: string; procurement_plan: string; estimated_amount: number; status: string; recommended_supplier: string | null; evaluated_amount: number | null; purchase_order: string | null }
export interface PaymentRequest { name: string; company: string; request_date: string; payee: string; description: string; amount: number; status: string; payment_entry: string | null }
export interface AuditQuery { name: string; company: string; query_date: string; query_type: string; severity: string; subject: string; assigned_to: string; response_due_date: string; status: string }

export function money(value: unknown) { return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(Number(value || 0)); }
export function today() { return new Date().toISOString().slice(0, 10); }
