import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const EDIT_PAYLOAD = {
  values: {
    first_name: "Aondo", middle_name: null, last_name: "Terver", gender: "Male", date_of_birth: "1980-05-01",
    date_of_joining: "2010-01-04", department: "Works - MKD", designation: null, status: "Active",
    relieving_date: null, reason_for_leaving: null, employee_number: "MKD/001", dtmgp_grade_level: "GL 08",
    dtmgp_step: 3, dtmgp_rank: null, dtmgp_schedule_of_duty: null, dtmgp_verification_status: "Pending",
    dtmgp_date_of_first_appointment: "2010-01-04", dtmgp_date_of_present_appointment: null, date_of_retirement: "2040-05-01",
    dtmgp_local_govt_of_payment: "Makurdi", salary_mode: "Bank", bank_name: "Zenith Bank Plc", bank_ac_no: "1012345678", cell_number: null, personal_email: null, person_to_be_contacted: null,
    relation: null, emergency_phone_number: null, dtmgp_lg_of_origin: null, dtmgp_council_ward: null,
    dtmgp_bvn: null, dtmgp_nin: null, dtmgp_qualifications: null,
  },
  readonly: { name: "HR-EMP-0001", employee_name: "Aondo Terver", company: "Makurdi Local Government Area", image: null, dtmgp_retire_year_by_age: "2040-05-01", dtmgp_retire_year_by_appointment: "2045-01-04" },
  pay_points: ["Gboko", "Makurdi"],
  salary_modes: ["Bank", "Cash", "Cheque"],
  banks: ["First Bank of Nigeria Limited", "Zenith Bank Plc"],
};

const apiRequest = vi.fn((path: string, _options?: RequestInit): Promise<unknown> =>
  Promise.resolve(path.includes("get_employee_for_edit") ? EDIT_PAYLOAD : { name: "HR-EMP-0001", employee_name: "Aondo Terver", changed: ["dtmgp_grade_level"] }),
);
const uploadFile = vi.fn((_file: File, _params: Record<string, unknown>) => Promise.resolve({ file_url: "/private/files/employee-photo.jpg" }));
vi.mock("@/services/api", () => ({
  apiRequest: (path: string, options?: RequestInit) => apiRequest(path, options),
  uploadFile: (file: File, params: Record<string, unknown>) => uploadFile(file, params),
}));
const CAPTURED = new File(["x"], "employee-photo.jpg", { type: "image/jpeg" });
const CameraCaptureStub = { emits: ["captured", "cancel"], template: '<button class="fake-capture" type="button" @click="$emit(\'captured\', file)">Capture</button>', data: () => ({ file: CAPTURED }) };

// jsdom has no object URLs; the modal uses one to preview the captured photo.
URL.createObjectURL = vi.fn(() => "blob:preview");
URL.revokeObjectURL = vi.fn();

import EmployeeEditModal from "./EmployeeEditModal.vue";

const OPTIONS = { departments: ["Works - MKD"], designations: ["Clerk"], genders: ["Male", "Female"], statuses: ["Active", "Inactive", "Suspended", "Left"], verification_statuses: ["Pending", "Verified", "Review Due"] };

async function mountModal() {
  const wrapper = mount(EmployeeEditModal, { props: { employee: "HR-EMP-0001", options: OPTIONS }, global: { stubs: { CameraCapture: CameraCaptureStub } } });
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
  beforeEach(() => { apiRequest.mockClear(); uploadFile.mockClear(); });

  it("loads the record and sends only the changed fields", async () => {
    const wrapper = await mountModal();
    expect(wrapper.text()).toContain("Aondo Terver · HR-EMP-0001 · Makurdi LGA");
    expect(wrapper.text()).toContain("No changes");

    // Grade, step, rank, BVN and NIN sit on the default (Personal) tab.
    const personal = wrapper.findAll(".form-grid").find((grid) => grid.isVisible())!;
    const visibleLabels = personal.findAll("label.field > span:first-child").map((label) => label.text().replace("*", ""));
    expect(visibleLabels).toEqual(expect.arrayContaining(["Grade level", "Step", "Rank", "BVN", "NIN"]));
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

  it("validates bank details when salary mode is Bank", async () => {
    const wrapper = await mountModal();
    await openSection(wrapper, "Pay & bank");
    await inputLabelled(wrapper, "Account number (NUBAN)").setValue("12345");
    expect(wrapper.text()).toContain("Must be a 10-digit NUBAN account number");
    await inputLabelled(wrapper, "Account number (NUBAN)").setValue("");
    expect(wrapper.text()).toContain("Required when salary mode is Bank");

    await inputLabelled(wrapper, "Account number (NUBAN)").setValue("2098765432");
    await inputLabelled(wrapper, "Bank").setValue("First Bank of Nigeria Limited");
    await wrapper.find("form").trigger("submit");
    await flushPromises();
    const [, options] = apiRequest.mock.calls.at(-1)!;
    expect(JSON.parse(String(options!.body)).values).toEqual({ bank_ac_no: "2098765432", bank_name: "First Bank of Nigeria Limited" });
  });

  it("takes a camera photo, applies it only on save, and offers no file picker", async () => {
    const wrapper = await mountModal();
    expect(wrapper.find("input[type=file]").exists()).toBe(false);
    await wrapper.findAll(".employee-edit-photo-actions button").find((button) => button.text().includes("Take photo"))!.trigger("click");
    await wrapper.find(".fake-capture").trigger("click");
    expect(uploadFile).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain("Save 1 change");

    await wrapper.find("form").trigger("submit");
    await flushPromises();
    expect(uploadFile).toHaveBeenCalledWith(CAPTURED, { doctype: "Employee", docname: "HR-EMP-0001", isPrivate: true });
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("set_employee_image"), expect.objectContaining({ body: JSON.stringify({ employee: "HR-EMP-0001", file_url: "/private/files/employee-photo.jpg" }) }));
    expect(apiRequest.mock.calls.some(([path]) => path.includes("update_employee"))).toBe(false);
    expect(wrapper.emitted("saved")![0][0]).toMatchObject({ changed: ["image"] });
  });
});
