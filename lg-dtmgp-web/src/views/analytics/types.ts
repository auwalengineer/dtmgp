export interface Freshness { status: "fresh" | "stale" | "missing"; last_updated: string | null }
export interface Metric { key: string; label: string; domain: string; source: string; format: "number" | "percent" | "currency"; value: number; drilldown: string; freshness: Freshness; classification: string }
export interface Completeness { percent: number; sources: { source: string; status: string; last_updated: string | null }[]; missing: string[]; stale: string[] }
export interface Dashboard { scope: string; period: { from_date: string; to_date: string; label: string }; generated_at: string; can_compare_lgas: boolean; domains: Record<string, boolean>; metrics: Metric[]; completeness: Completeness }
export interface Scorecard { company: string; score: number | null; rank: number | null; completeness: number; missing: string[]; stale: string[]; metrics: Record<string, number | null> }
export interface TrendMonth { key: string; label: string; revenue: number; payments: number; projects: number; returns: number }
export interface AlertItem { type: string; severity: string; company: string; title: string; age_days: number | null; to: string }
export interface MapPoint { name: string; label: string; company: string; status: string; latitude: number; longitude: number }

export function formatMetric(metric: Pick<Metric, "format" | "value">) {
  if (metric.format === "currency") return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(metric.value);
  if (metric.format === "percent") return `${metric.value.toLocaleString("en-NG")}%`;
  return metric.value.toLocaleString("en-NG");
}

export function scoreLabel(row: Pick<Scorecard, "score" | "missing" | "stale">) {
  if (row.score === null) return row.missing.length ? `Not ranked: ${row.missing.join(", ")} missing` : `Not ranked: ${row.stale.join(", ")} stale`;
  return `${row.score.toFixed(1)}%`;
}
