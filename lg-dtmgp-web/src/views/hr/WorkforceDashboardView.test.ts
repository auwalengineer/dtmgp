import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const row = (label: string, value: number) => ({ label, value });
const SUMMARY = {
  scope: { companies: 23, is_statewide: true },
  totals: { total: 12, active: 10, left: 2, verified: 6, pending_verification: 4, retiring_12m: 1, past_retirement: 1, joined_this_year: 2, average_age: 41.5 },
  breakdowns: {
    lga: [
      { label: "Makurdi LGA", company: "Makurdi Local Government Area", value: 7, verified: 5 },
      { label: "Gboko LGA", company: "Gboko Local Government Area", value: 3, verified: 1 },
    ],
    status: [row("Active", 10), row("Left", 2)],
    gender: [row("Female", 5), row("Male", 5)],
    grade_level: [row("GL 06", 4), row("GL 10", 6)],
    verification: [row("Verified", 6), row("Pending", 4)],
    age_band: [row("25 - 34", 4), row("35 - 44", 6)],
    department: [row("Works", 6), row("Health", 4)],
    retirements_by_year: [row("Overdue", 1), row("2026", 1)],
    appointments_by_year: [row("2025", 1), row("2026", 2)],
  },
};

const apiRequest = vi.fn((_path: string) => Promise.resolve(SUMMARY as unknown));
vi.mock("@/services/api", () => ({ apiRequest: (path: string) => apiRequest(path) }));

import { useSessionStore } from "@/stores/session";
import WorkforceDashboardView from "./WorkforceDashboardView.vue";

describe("WorkforceDashboardView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
  });

  it("loads the overall summary without forcing an LGA and renders totals and breakdowns", async () => {
    const session = useSessionStore();
    session.canChangeLga = true;
    session.allowedLgas = ["Makurdi Local Government Area", "Gboko Local Government Area"];
    const wrapper = mount(WorkforceDashboardView, { global: { stubs: { ReportActions: true } } });
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith("/api/method/dtmgp.api.v1.people.get_workforce_dashboard");
    expect(wrapper.text()).toContain("All 23 LGAs in your scope");
    expect(wrapper.text()).toContain("60%");
    expect(wrapper.text()).toContain("Makurdi LGA");
    expect(wrapper.text()).toContain("1 active past retirement date");

    await wrapper.find("select").setValue("Gboko Local Government Area");
    await flushPromises();
    expect(apiRequest).toHaveBeenLastCalledWith(expect.stringContaining("company=Gboko%20Local%20Government%20Area"));
  });

  it("hides the LGA picker for single-LGA users and shows an error for a malformed response", async () => {
    apiRequest.mockResolvedValueOnce({ totals: {} });
    const wrapper = mount(WorkforceDashboardView, { global: { stubs: { ReportActions: true } } });
    await flushPromises();
    expect(wrapper.find("select").exists()).toBe(false);
    expect(wrapper.find("[role=alert]").exists()).toBe(true);
  });
});
