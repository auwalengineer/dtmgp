import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const row = (label: string, value: number) => ({ label, value });
const GRADE = { "Junior (GL 01-06)": 2, "Senior (GL 07-12)": 4, "Management (GL 13-17)": 1 };
function lga(name: string, active: number, extra: Record<string, unknown> = {}) {
  return {
    company: `${name} Local Government Area`, label: `${name} LGA`, total: active + 1, active, left: 1, verified: Math.floor(active / 2),
    pending_verification: active - Math.floor(active / 2), retiring_12m: 1, past_retirement: 0, joined_this_year: 0,
    average_age: active ? 42 : null, average_service: active ? 12 : null, male: Math.ceil(active / 2), female: Math.floor(active / 2),
    share_pct: 0, verified_pct: active ? 50 : 0, female_pct: active ? 40 : 0, management_pct: 10, bvn_pct: 80, nin_pct: 70,
    photo_pct: 20, bank_pct: 90, phone_pct: 50, first_appointment_pct: 60, grade_bands: active ? GRADE : { "Junior (GL 01-06)": 0, "Senior (GL 07-12)": 0, "Management (GL 13-17)": 0 },
    ...extra,
  };
}
const SUMMARY = {
  scope: { companies: 3, is_statewide: true },
  totals: {
    total: 12, active: 10, left: 2, suspended_or_inactive: 1, verified: 6, pending_verification: 4, male: 5, female: 5,
    retiring_12m: 1, retiring_5y: 3, past_retirement: 1, joined_this_year: 2, average_age: 41.5, average_service: 11.2,
    completeness: { bvn: 80, nin: 70, photo: 20, bank: 90, phone: 50, first_appointment: 60 },
  },
  breakdowns: {
    lga: [{ label: "Makurdi LGA", company: "Makurdi Local Government Area", value: 7, verified: 5 }],
    status: [row("Active", 10), row("Left", 2)], gender: [row("Female", 5), row("Male", 5)],
    grade_level: [row("GL 06", 4), row("GL 10", 6)], grade_band: [row("Junior (GL 01-06)", 4), row("Senior (GL 07-12)", 6)],
    verification: [row("Verified", 6), row("Pending", 4)], age_band: [row("25 - 34", 4), row("35 - 44", 6)],
    service_band: [row("5 - 9 years", 4), row("10 - 19 years", 6)], department: [row("Works", 6), row("Health", 4)],
    designation: [row("Clerk", 6)], rank: [row("Senior Officer", 3)], salary_mode: [row("Bank", 9), row("Cash", 1)],
    data_completeness: [{ label: "BVN", value: 80, count: 8 }, { label: "NIN", value: 70, count: 7 }],
    retirements_by_year: [row("Overdue", 1), row("2026", 1)], appointments_by_year: [row("2025", 1), row("2026", 2)],
  },
  lga_comparison: [lga("Makurdi", 7, { female_pct: 60, past_retirement: 1 }), lga("Gboko", 3, { female_pct: 20 }), lga("Ado", 0, { total: 0, left: 0 })],
  comparison_metrics: [
    { key: "active", label: "Active staff", unit: "count" },
    { key: "female_pct", label: "Female", unit: "pct" },
    { key: "average_age", label: "Average age", unit: "years" },
  ],
};

const apiRequest = vi.fn((_path: string) => Promise.resolve(SUMMARY as unknown));
vi.mock("@/services/api", () => ({ apiRequest: (path: string) => apiRequest(path) }));

import ReportActions from "@/components/ReportActions.vue";
import { useSessionStore } from "@/stores/session";
import WorkforceDashboardView from "./WorkforceDashboardView.vue";

function mountView() {
  return mount(WorkforceDashboardView, { global: { stubs: { ReportActions: true } } });
}

describe("WorkforceDashboardView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
  });

  it("loads the overall summary and renders KPIs, comparison and distributions", async () => {
    const session = useSessionStore();
    session.canChangeLga = true;
    session.allowedLgas = ["Makurdi Local Government Area", "Gboko Local Government Area"];
    const wrapper = mountView();
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith("/api/method/dtmgp.api.v1.people.get_workforce_dashboard");
    expect(wrapper.text()).toContain("All 3 LGAs in your scope");
    expect(wrapper.text()).toContain("80% / 70%"); // BVN / NIN captured (rounded in the tile)
    expect(wrapper.text()).toContain("1 with no active staff records");
    expect(wrapper.text()).toContain("Years of service");
    expect(wrapper.findAll(".workforce-table tbody tr")).toHaveLength(3);

    await wrapper.find(".workforce-scope select").setValue("Gboko Local Government Area");
    await flushPromises();
    expect(apiRequest).toHaveBeenLastCalledWith(expect.stringContaining("company=Gboko%20Local%20Government%20Area"));
  });

  it("ranks LGAs by the chosen metric and shows highest and lowest", async () => {
    const wrapper = mountView();
    await flushPromises();
    await wrapper.find(".workforce-scope.compact select").setValue("female_pct");
    const extremes = wrapper.find(".workforce-extremes").text();
    expect(extremes).toContain("Highest: Makurdi LGA 60%");
    expect(extremes).toContain("Lowest: Gboko LGA 20%");
    const ranked = wrapper.findAll(".workforce-card.wide")[0].findAll(".bar-list-label").map((label) => label.text());
    expect(ranked.slice(0, 2)).toEqual(["Makurdi LGA", "Gboko LGA"]);
  });

  it("sorts the comparison table, hides empty LGAs and exports the server-approved columns", async () => {
    const wrapper = mountView();
    await flushPromises();
    const firstColumn = () => wrapper.findAll(".workforce-table tbody th").map((cell) => cell.text());
    expect(firstColumn()).toEqual(["Makurdi LGA", "Gboko LGA", "Ado LGA"]);

    await wrapper.findAll(".workforce-table thead button").find((button) => button.text().startsWith("LGA"))!.trigger("click");
    expect(firstColumn()).toEqual(["Ado LGA", "Gboko LGA", "Makurdi LGA"]);

    await wrapper.find(".workforce-toggle input").setValue(true);
    expect(firstColumn()).not.toContain("Ado LGA");

    // Must equal REPORT_COLUMNS["hr.lga-comparison"] in dtmgp/api/v1/report_exports.py.
    expect(wrapper.findComponent(ReportActions).props("columns")).toEqual([
      "LGA", "Active", "Share %", "Verified %", "Female %", "Avg age", "Avg service (yrs)", "GL 13+ %", "Retiring 12m",
      "Past retirement", "Appointed this yr", "BVN %", "NIN %", "Photo %", "Bank %",
    ]);
  });

  it("hides the comparison for a single-LGA scope and shows an error for a malformed response", async () => {
    apiRequest.mockResolvedValueOnce({ ...SUMMARY, scope: { companies: 1, is_statewide: false }, lga_comparison: [SUMMARY.lga_comparison[0]] });
    const single = mountView();
    await flushPromises();
    expect(single.find("#lga-comparison-title").exists()).toBe(false);
    expect(single.find(".workforce-scope select").exists()).toBe(false);

    apiRequest.mockResolvedValueOnce({ totals: {} });
    const broken = mountView();
    await flushPromises();
    expect(broken.find("[role=alert]").exists()).toBe(true);
  });
});
