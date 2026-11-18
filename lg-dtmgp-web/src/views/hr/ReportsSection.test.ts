import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const OPTIONS = {
  departments: [{ value: "Works - MKD", label: "Works" }], statuses: ["Active", "Suspended", "Inactive", "Left", "All"],
  group_by: [{ value: "department", label: "Department" }, { value: "grade_band", label: "Grade band" }],
  dimensions: [{ value: "grade_level", label: "Grade level" }, { value: "gender", label: "Gender" }],
  leave_groups: [{ value: "leave_type", label: "Leave type" }], retirement_horizons: [12, 24, 36, 60], is_statewide: false,
};
const STRENGTH = {
  columns: [{ key: "group", label: "Department", type: "text" }, { key: "active", label: "Active", type: "int" }, { key: "share_pct", label: "% of active", type: "pct" }],
  rows: [{ group: "Works", active: 3, share_pct: 75 }, { group: "Health", active: 1, share_pct: 25 }],
  totals: { group: "Total", active: 4, share_pct: 100 },
  summary: [{ label: "Active staff", value: 4 }, { label: "Female share", value: 50, unit: "pct" }],
  note: null, truncated: false,
};
const ROLL = {
  columns: [{ key: "name", label: "Staff ID", type: "text" }, { key: "employee_name", label: "Name", type: "text" }, { key: "date_of_birth", label: "Date of birth", type: "date" }],
  rows: Array.from({ length: 12 }, (_value, index) => ({ name: `HR-${index}`, employee_name: index === 4 ? "Amina Bello" : `Staff ${index}`, date_of_birth: "1990-03-05" })),
  totals: null, summary: [{ label: "Staff listed", value: 12 }], note: null, truncated: false,
};
const apiRequest = vi.fn((path: string) => {
  if (path.includes("get_hr_report_options")) return Promise.resolve(OPTIONS);
  if (path.includes("report=nominal-roll")) return Promise.resolve(ROLL);
  return Promise.resolve(STRENGTH);
});
vi.mock("@/services/api", () => ({ apiRequest: (path: string) => apiRequest(path) }));

import { useSessionStore } from "@/stores/session";
import ReportsSection from "./ReportsSection.vue";

function mountReports(item: string) {
  mockRouteParams = { section: "hr-reports", item };
  setActivePinia(createPinia());
  useSessionStore().activeLga = "Makurdi Local Government Area";
  return mount(ReportsSection);
}
const lastQuery = () => new URLSearchParams(String(apiRequest.mock.calls.at(-1)?.[0]).split("?")[1]);

describe("ReportsSection", () => {
  beforeEach(() => { apiRequest.mockClear(); });

  it("lists every report and opens the one named in the route", async () => {
    const wrapper = mountReports("staff-strength-report");
    await flushPromises();
    for (const label of ["Nominal Roll", "Staff Strength Report", "Retirement Forecast", "Appointments & Exits", "Verification Report", "Records Completeness"]) {
      expect(wrapper.text()).toContain(label);
    }
    expect(lastQuery().get("report")).toBe("staff-strength");
    expect(lastQuery().get("company")).toBe("Makurdi Local Government Area");
    expect(lastQuery().get("group_by")).toBe("department");
  });

  it("renders summary tiles, formatted cells and a totals row", async () => {
    const wrapper = mountReports("staff-strength-report");
    await flushPromises();
    expect(wrapper.find(".hr-report-summary").text()).toContain("50%");
    expect(wrapper.findAll("tbody tr")).toHaveLength(2);
    expect(wrapper.find("tfoot").text()).toContain("Total");
    expect(wrapper.find("tfoot").text()).toContain("100%");
  });

  it("reloads with the chosen filters", async () => {
    const wrapper = mountReports("staff-strength-report");
    await flushPromises();
    await wrapper.find(".hr-report-filters select").setValue("grade_band");
    await flushPromises();
    expect(lastQuery().get("group_by")).toBe("grade_band");
    const department = wrapper.findAll(".hr-report-filters select").at(-1)!;
    await department.setValue("Works - MKD");
    await flushPromises();
    expect(lastQuery().get("department")).toBe("Works - MKD");
  });

  it("sorts by a column header, numbers largest first", async () => {
    const wrapper = mountReports("staff-strength-report");
    await flushPromises();
    await wrapper.findAll(".hr-report-sort")[1].trigger("click");
    expect(wrapper.findAll("tbody tr")[0].text()).toContain("Works");
    expect(wrapper.findAll("th")[1].attributes("aria-sort")).toBe("descending");
    await wrapper.findAll(".hr-report-sort")[1].trigger("click");
    expect(wrapper.findAll("tbody tr")[0].text()).toContain("Health");
  });

  it("searches a listing report and formats dates", async () => {
    const wrapper = mountReports("nominal-roll");
    await flushPromises();
    expect(lastQuery().get("status")).toBe("Active");
    expect(wrapper.find("tbody").text()).toContain("05 Mar 1990");
    await wrapper.find('input[aria-label="Search this report"]').setValue("amina");
    expect(wrapper.findAll("tbody tr")).toHaveLength(1);
    expect(wrapper.text()).toContain("1 of 12 rows");
  });
});
