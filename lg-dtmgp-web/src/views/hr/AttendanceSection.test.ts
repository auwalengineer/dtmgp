import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const apiRequest = vi.fn();
vi.mock("@/services/api", () => ({ apiRequest: (...args: unknown[]) => apiRequest(...args) }));

import AttendanceSection from "./AttendanceSection.vue";
import type { AttendanceItem, AttendanceSummary } from "./types";

const SUMMARY: AttendanceSummary = { date: "2026-09-19", present: 2, absent: 1, on_leave: 0, half_day: 0, late_entries: 1 };
const ITEMS: AttendanceItem[] = [
  { name: "ATT-1", employee: "HR-0001", employee_name: "Amina Bello", attendance_date: "2026-09-19", status: "Present", late_entry: 1, early_exit: 0 },
  { name: "ATT-2", employee: "HR-0002", employee_name: "Chidi Okoro", attendance_date: "2026-09-19", status: "Absent", late_entry: 0, early_exit: 0 },
  { name: "ATT-3", employee: "HR-0003", employee_name: "Fatima Sule", attendance_date: "2026-09-19", status: "Present", late_entry: 0, early_exit: 0 },
];

function mountSection(routeItem?: string) {
  mockRouteParams = routeItem ? { section: "attendance", item: routeItem } : { section: "attendance" };
  return mount(AttendanceSection, { props: { attendanceSummary: SUMMARY, attendanceItems: ITEMS } });
}

describe("AttendanceSection", () => {
  it("defaults to Attendance Records when no item is in the route", () => {
    const wrapper = mountSection();
    expect(wrapper.find(".hr-item-tabs button.active").text()).toBe("Attendance Records");
    expect(wrapper.text()).toContain("Present today");
  });

  it("renders every Attendance nav leaf as its own item tab", () => {
    const wrapper = mountSection();
    const labels = wrapper.findAll(".hr-item-tabs button").map((button) => button.text());
    expect(labels).toEqual(["Attendance Records", "Shift Assignments", "Late Arrivals", "Absent Staff", "Attendance Reports"]);
  });

  it("Late Arrivals filters attendanceItems client-side to late_entry rows", () => {
    const wrapper = mountSection("late-arrivals");
    expect(wrapper.text()).toContain("Amina Bello");
    expect(wrapper.text()).not.toContain("Chidi Okoro");
    expect(wrapper.text()).not.toContain("Fatima Sule");
  });

  it("Absent Staff filters attendanceItems client-side to Absent rows", () => {
    const wrapper = mountSection("absent-staff");
    expect(wrapper.text()).toContain("Chidi Okoro");
    expect(wrapper.text()).not.toContain("Amina Bello");
    expect(wrapper.text()).not.toContain("Fatima Sule");
  });

  it("shows an honest empty state for Shift Assignments instead of fabricated rows", () => {
    const wrapper = mountSection("shift-assignments");
    expect(wrapper.text()).toContain("Shift assignments will appear here once a shift-assignment service is available for this LGA.");
    expect(wrapper.findAll(".staff-table tbody tr").length).toBe(0);
  });

  it("switches items without ever calling the API", async () => {
    const wrapper = mountSection();
    const tabs = wrapper.findAll(".hr-item-tabs button");
    for (const tab of tabs) await tab.trigger("click");
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
