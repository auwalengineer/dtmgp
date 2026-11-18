import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const PROFILE = { name: "HR-0001", employee_name: "Amina Bello", image: null, company: "Makurdi Local Government Area", department: "Finance", designation: "Officer", status: "Active", gender: "Female", date_of_birth: "1990-01-01", date_of_joining: "2020-01-01", grade_level: "GL 08", verification_status: "Verified", cell_number: "0800", personal_email: "amina@example.com", emergency_contact: { person_to_be_contacted: "Bala Bello", relation: "Spouse", emergency_phone_number: "0801" }, internal_work_history: [], external_work_history: [] };
const DOCUMENTS = [{ name: "FILE-1", file_name: "contract.pdf", file_url: "/files/contract.pdf", is_private: 1, creation: "2026-01-01" }];
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("get_employee_profile")) return Promise.resolve({ ...PROFILE });
  if (path.includes("set_employee_image")) return Promise.resolve({ name: "HR-0001", image: JSON.parse(String(_options?.body)).file_url });
  if (path.includes("list_employee_documents")) return Promise.resolve(DOCUMENTS);
  if (path.includes("record_type=next_of_kin")) return Promise.resolve([{ name: "NOK-1", full_name: "Bala Bello", relationship: "Spouse", phone: "0801", is_primary: 1 }]);
  if (path.includes("list_restricted_hr_records")) return Promise.resolve([]);
  return Promise.resolve({});
});
const uploadFile = vi.fn((_file: File, _params: Record<string, unknown>) => Promise.resolve({ file_url: "/private/files/amina.png" }));
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args), uploadFile: (...args: [File, Record<string, unknown>]) => uploadFile(...args) }));

import StaffSection from "./StaffSection.vue";
import type { Employee } from "./types";

const CAPTURED = new File(["x"], "employee-photo.jpg", { type: "image/jpeg" });
// Stands in for the real getUserMedia component, which jsdom can't run.
const CameraCaptureStub = { emits: ["captured", "cancel"], template: '<button class="fake-capture" type="button" @click="$emit(\'captured\', file)">Capture</button>', data: () => ({ file: CAPTURED }) };

const EMPLOYEES: Employee[] = [{ name: "HR-0001", employee_name: "Amina Bello", first_name: "Amina", last_name: "Bello", company: "Makurdi Local Government Area", department: "Finance", designation: "Officer", status: "Active", date_of_joining: "2020-01-01", date_of_birth: "1990-01-01", gender: "Female", dtmgp_grade_level: "GL 08", dtmgp_verification_status: "Verified" }];

function mountSection(routeItem?: string) {
  mockRouteParams = routeItem ? { section: "staff", item: routeItem } : { section: "staff" };
  return mount(StaffSection, { props: { employees: EMPLOYEES, total: 1, page: 1, pageSize: 25, search: "", department: "", departmentOptions: ["Finance"], canManage: true, formOptions: { departments: [], designations: [], genders: [], statuses: [], verification_statuses: [] } }, global: { stubs: { CameraCapture: CameraCaptureStub } } });
}

describe("StaffSection", () => {
  beforeEach(() => { apiRequest.mockClear(); uploadFile.mockClear(); });

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

  it("shows the employee photo in the directory and falls back to initials", async () => {
    const withPhoto = { ...EMPLOYEES[0], image: "/files/amina.png" };
    const wrapper = mount(StaffSection, { props: { employees: [withPhoto, { ...EMPLOYEES[0], name: "HR-0002", employee_name: "Tersoo Iorliam" }], total: 2, page: 1, pageSize: 25, search: "", department: "", departmentOptions: [], canManage: false, formOptions: { departments: [], designations: [], genders: [], statuses: [], verification_statuses: [] } } });
    const avatars = wrapper.findAll(".employee-avatar");
    expect(avatars[0].find("img").attributes("src")).toBe("/files/amina.png");
    expect(avatars[1].find("img").exists()).toBe(false);
    expect(avatars[1].text()).toBe("TI");

    await avatars[0].find("img").trigger("error");
    expect(wrapper.findAll(".employee-avatar")[0].text()).toBe("AB");
  });

  it("takes the photo with the device camera and saves it as a private file on the employee", async () => {
    const wrapper = mountSection("staff-profiles");
    await wrapper.find("select").setValue("HR-0001");
    await flushPromises();
    expect(wrapper.find(".employee-avatar.large").text()).toBe("AB");
    // Camera-only: there is no file picker anywhere in the profile.
    expect(wrapper.find("input[type=file]").exists()).toBe(false);

    await wrapper.findAll(".employee-photo-actions button").find((button) => button.text().includes("Take photo"))!.trigger("click");
    await wrapper.find(".fake-capture").trigger("click");
    await flushPromises();

    expect(uploadFile).toHaveBeenCalledWith(CAPTURED, { doctype: "Employee", docname: "HR-0001", isPrivate: true });
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("set_employee_image"), expect.objectContaining({ method: "POST" }));
    expect(wrapper.find(".employee-avatar.large img").attributes("src")).toBe("/private/files/amina.png");
    expect(wrapper.find(".camera-modal").exists()).toBe(false);
    expect(wrapper.emitted("photo-changed")).toHaveLength(1);
  });
});
