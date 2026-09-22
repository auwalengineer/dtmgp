export interface Dashboard { scope: string; lga_count: number; revenue: { assessed: number; collected: number; outstanding: number }; procurement: { planned: number; active: number; pending_approval: number }; payments: { pending: number; paid: number }; audit: { open_queries: number; overdue_queries: number }; can_manage: boolean }
export interface Options { departments: string[]; accounts: string[]; cost_centers: string[]; fiscal_years: string[]; revenue_heads: { name: string; revenue_name: string }[]; procurement_plans: { name: string; title: string }[] }
export interface RevenueHead { name: string; company: string; revenue_code: string; revenue_name: string; rate_type: string; default_rate: number; disabled: number }
export interface RevenueAssessment { name: string; company: string; revenue_head: string; taxpayer_name: string; assessment_date: string; due_date: string; amount: number; amount_paid: number; status: string }
export interface RevenueReceipt { name: string; company: string; assessment: string; posting_date: string; amount: number; payment_channel: string; bank_reference: string; docstatus: number }
export interface ProcurementPlan { name: string; company: string; fiscal_year: string; title: string; procurement_category: string; procurement_method: string; estimated_amount: number; status: string }
export interface ProcurementCase { name: string; company: string; title: string; procurement_plan: string; estimated_amount: number; status: string; recommended_supplier: string | null; evaluated_amount: number | null; purchase_order: string | null }
export interface PaymentRequest { name: string; company: string; request_date: string; payee: string; description: string; amount: number; status: string; payment_entry: string | null }
export interface AuditQuery { name: string; company: string; query_date: string; query_type: string; severity: string; subject: string; assigned_to: string; response_due_date: string; status: string }
export interface Allocation { name: string; company: string; fiscal_year: string; tier: string; source: string; tranche_period: string; amount: number; expected_date: string | null; received_date: string | null; bank_reference: string | null; status: string; distributed_total: number }
export interface AllocationDistribution { name: string; allocation: string; department: string; purpose: string; amount: number; company: string; status: string }
export interface Contract { name: string; company: string; title: string; procurement_case: string; contractor: string; contract_value: number; start_date: string; end_date: string | null; status: string; completion_certificate_reference: string | null }
export interface ContractMilestone { name: string; contract: string; title: string; due_date: string | null; amount: number; status: string; certified_date: string | null; payment_request: string | null; company: string }
export interface ContractVariation { name: string; company: string; contract: string; variation_type: string; requested_date: string; amount_change: number; days_change: number | null; status: string }
export interface Budget { name: string; company: string; fiscal_year: string; budget_against: string; cost_center: string | null; project: string | null; docstatus: number; amended_from: string | null; total_budget: number }
export interface AccountRow { name: string; account_name: string; parent_account: string | null; is_group: number; root_type: string; account_type: string | null }
export interface JournalEntryRow { name: string; posting_date: string; voucher_type: string; company: string; total_debit: number; user_remark: string | null }
export interface GLEntryRow { name: string; posting_date: string; account: string; debit: number; credit: number; against: string | null; voucher_type: string; voucher_no: string; company: string }
export interface TrialBalanceRow { account: string; root_type: string; debit: number; credit: number }
export interface BudgetPerformanceRow { account: string; budget: number; actual: number; variance: number }
export interface PurchaseReceiptRow { name: string; posting_date: string; supplier: string; grand_total: number; status: string }
export interface ApprovalLimit { name: string; company: string; transaction_type: string; approving_role: string; minimum_amount: number; maximum_amount: number; active: number }

export function money(value: unknown) { return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(Number(value || 0)); }
export function today() { return new Date().toISOString().slice(0, 10); }
