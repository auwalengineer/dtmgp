import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const apiRequest = vi.fn();
vi.mock("@/services/api", () => ({ apiRequest: (...args: unknown[]) => apiRequest(...args) }));

import StaffSection from "./StaffSection.vue";
import type { Employee } from "./types";

const EMPLOYEES: Employee[] = [{ name: "HR-0001", employee_name: "Amina Bello", first_name: "Amina", last_name: "Bello", company: "Makurdi Local Government Area", department: "Finance", designation: "Officer", status: "Active", date_of_joining: "2020-01-01", date_of_birth: "1990-01-01", gender: "Female", dtmgp_grade_level: "GL 08", dtmgp_verification_status: "Verified" }];

function mountSection(routeItem?: string) {
  mockRouteParams = routeItem ? { section: "staff", item: routeItem } : { section: "staff" };
  return mount(StaffSection, { props: { employees: EMPLOYEES, total: 1, page: 1, pageSize: 25, search: "", department: "", departmentOptions: ["Finance"], canManage: true } });
}

describe("StaffSection", () => {
  it("defaults to Staff Directory when no item is in the route", () => {
    const wrapper = mountSection();
    expect(wrapper.find(".hr-item-tabs button.active").text()).toBe("Staff Directory");
    expect(wrapper.find(".staff-table").exists()).toBe(true);
    expect(wrapper.text()).toContain("Amina Bello");
  });

  it("renders every Staff nav leaf as its own item tab", () => {
    const wrapper = mountSection();
    const labels = wrapper.findAll(".hr-item-tabs button").map((button) => button.text());
    expect(labels).toEqual(["Staff Directory", "Staff Profiles", "Digital Personnel Files", "Employment History", "Next of Kin", "Staff Documents"]);
  });

  it("shows an honest empty state for a not-yet-wired item instead of directory data", async () => {
    const wrapper = mountSection("next-of-kin");
    expect(wrapper.text()).toContain("Only a single emergency contact per staff member is currently recorded");
    expect(wrapper.text()).not.toContain("Amina Bello");
  });

  it("switches items without ever calling the API", async () => {
    const wrapper = mountSection();
    const tabs = wrapper.findAll(".hr-item-tabs button");
    for (const tab of tabs) await tab.trigger("click");
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
