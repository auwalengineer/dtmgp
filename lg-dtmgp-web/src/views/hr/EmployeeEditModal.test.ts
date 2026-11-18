import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const EDIT_PAYLOAD = {
  values: {
    first_name: "Aondo", middle_name: null, last_name: "Terver", gender: "Male", date_of_birth: "1980-05-01",
    date_of_joining: "2010-01-04", department: "Works - MKD", designation: null, status: "Active",
    relieving_date: null, reason_for_leaving: null, employee_number: "MKD/001", dtmgp_grade_level: "GL 08",
    dtmgp_step: 3, dtmgp_rank: null, dtmgp_schedule_of_duty: null, dtmgp_verification_status: "Pending",
    dtmgp_date_of_first_appointment: "2010-01-04", dtmgp_date_of_present_appointment: null, date_of_retirement: "2040-05-01",
    dtmgp_local_govt_of_payment: "Makurdi", cell_number: null, personal_email: null, person_to_be_contacted: null,
    relation: null, emergency_phone_number: null, dtmgp_lg_of_origin: null, dtmgp_council_ward: null,
    dtmgp_bvn: null, dtmgp_nin: null, dtmgp_qualifications: null,
  },
  readonly: { name: "HR-EMP-0001", employee_name: "Aondo Terver", company: "Makurdi Local Government Area", image: null, dtmgp_retire_year_by_age: "2040-05-01", dtmgp_retire_year_by_appointment: "2045-01-04" },
  pay_points: ["Gboko", "Makurdi"],
};

const apiRequest = vi.fn((path: string, _options?: RequestInit): Promise<unknown> =>
  Promise.resolve(path.includes("get_employee_for_edit") ? EDIT_PAYLOAD : { name: "HR-EMP-0001", employee_name: "Aondo Terver", changed: ["dtmgp_grade_level"] }),
);
vi.mock("@/services/api", () => ({ apiRequest: (path: string, options?: RequestInit) => apiRequest(path, options) }));

import EmployeeEditModal from "./EmployeeEditModal.vue";

const OPTIONS = { departments: ["Works - MKD"], designations: ["Clerk"], genders: ["Male", "Female"], statuses: ["Active", "Inactive", "Suspended", "Left"], verification_statuses: ["Pending", "Verified", "Review Due"] };

async function mountModal() {
  const wrapper = mount(EmployeeEditModal, { props: { employee: "HR-EMP-0001", options: OPTIONS } });
  await flushPromises();
  return wrapper;
}
async function openSection(wrapper: Awaited<ReturnType<typeof mountModal>>, name: string) {
  await wrapper.findAll(".employee-edit-tabs button").find((button) => button.text() === name)!.trigger("click");
}
function inputLabelled(wrapper: Awaited<ReturnType<typeof mountModal>>, label: string) {
  return wrapper.findAll("label.field").find((field) => field.find("span").text().replace("*", "") === label)!.find("input, select, textarea");
}

describe("EmployeeEditModal", () => {
  beforeEach(() => { apiRequest.mockClear(); });

  it("loads the record and sends only the changed fields", async () => {
    const wrapper = await mountModal();
    expect(wrapper.text()).toContain("Aondo Terver · HR-EMP-0001 · Makurdi LGA");
    expect(wrapper.text()).toContain("No changes");

    await openSection(wrapper, "Service & appointment");
    await inputLabelled(wrapper, "Grade level").setValue("GL 09");
    await inputLabelled(wrapper, "Step").setValue("1");
    expect(wrapper.text()).toContain("Save 2 changes");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const [path, options] = apiRequest.mock.calls.at(-1)!;
    expect(path).toContain("update_employee");
    expect(JSON.parse(String(options!.body))).toEqual({ employee: "HR-EMP-0001", values: { dtmgp_grade_level: "GL 09", dtmgp_step: 1 } });
    expect(wrapper.emitted("saved")).toHaveLength(1);
  });

  it("blocks an invalid BVN and requires a relieving date when status is Left", async () => {
    const wrapper = await mountModal();
    await openSection(wrapper, "Origin & identity");
    await inputLabelled(wrapper, "BVN").setValue("12345");
    expect(wrapper.text()).toContain("Must be exactly 11 digits");

    await openSection(wrapper, "Service & appointment");
    await inputLabelled(wrapper, "Employment status").setValue("Left");
    expect(wrapper.text()).toContain("Required when status is Left");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(apiRequest.mock.calls.some(([path]) => path.includes("update_employee"))).toBe(false);
    expect(wrapper.find("[role=alert].login-error").text()).toContain("fix the highlighted fields");
  });
});
