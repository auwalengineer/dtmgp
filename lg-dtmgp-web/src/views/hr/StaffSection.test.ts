import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const PROFILE = { name: "HR-0001", employee_name: "Amina Bello", company: "Makurdi Local Government Area", department: "Finance", designation: "Officer", status: "Active", gender: "Female", date_of_birth: "1990-01-01", date_of_joining: "2020-01-01", grade_level: "GL 08", verification_status: "Verified", cell_number: "0800", personal_email: "amina@example.com", emergency_contact: { person_to_be_contacted: "Bala Bello", relation: "Spouse", emergency_phone_number: "0801" }, internal_work_history: [], external_work_history: [] };
const DOCUMENTS = [{ name: "FILE-1", file_name: "contract.pdf", file_url: "/files/contract.pdf", is_private: 1, creation: "2026-01-01" }];
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("get_employee_profile")) return Promise.resolve(PROFILE);
  if (path.includes("list_employee_documents")) return Promise.resolve(DOCUMENTS);
  if (path.includes("record_type=next_of_kin")) return Promise.resolve([{ name: "NOK-1", full_name: "Bala Bello", relationship: "Spouse", phone: "0801", is_primary: 1 }]);
  if (path.includes("list_restricted_hr_records")) return Promise.resolve([]);
  return Promise.resolve({});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args), uploadFile: vi.fn() }));

import StaffSection from "./StaffSection.vue";
import type { Employee } from "./types";

const EMPLOYEES: Employee[] = [{ name: "HR-0001", employee_name: "Amina Bello", first_name: "Amina", last_name: "Bello", company: "Makurdi Local Government Area", department: "Finance", designation: "Officer", status: "Active", date_of_joining: "2020-01-01", date_of_birth: "1990-01-01", gender: "Female", dtmgp_grade_level: "GL 08", dtmgp_verification_status: "Verified" }];

function mountSection(routeItem?: string) {
  mockRouteParams = routeItem ? { section: "staff", item: routeItem } : { section: "staff" };
  return mount(StaffSection, { props: { employees: EMPLOYEES, total: 1, page: 1, pageSize: 25, search: "", department: "", departmentOptions: ["Finance"], canManage: true } });
}

describe("StaffSection", () => {
  beforeEach(() => { apiRequest.mockClear(); });

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

  it("prompts for a staff member and makes no API call until one is picked", () => {
    const wrapper = mountSection("next-of-kin");
    expect(wrapper.text()).toContain("Select a staff member above to view their record.");
    expect(apiRequest).not.toHaveBeenCalled();
  });

  it("fetches the employee profile and restricted next-of-kin records", async () => {
    const wrapper = mountSection("next-of-kin");
    await wrapper.find("select").setValue("HR-0001");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_employee_profile?employee=HR-0001"));
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("record_type=next_of_kin"));
    expect(wrapper.text()).toContain("Bala Bello");
  });

  it("fetches documents for Staff Documents once a staff member is picked", async () => {
    const wrapper = mountSection("staff-documents");
    await wrapper.find("select").setValue("HR-0001");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("list_employee_documents?employee=HR-0001"));
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("record_type=staff_document"));
  });

  it("switches between already-wired items without ever calling the API", async () => {
    const wrapper = mountSection();
    const tabs = wrapper.findAll(".hr-item-tabs button");
    for (const tab of tabs) await tab.trigger("click");
    expect(apiRequest).not.toHaveBeenCalled();
  });
});
