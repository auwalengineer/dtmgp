import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const API_RESPONSES: Record<string, unknown> = {
  "dtmgp.api.v1.people.get_dashboard": { total: 3, active: 3, verified: 2, on_leave: 0, needs_attention: 1, can_manage: true },
  "dtmgp.api.v1.people.get_form_options": { departments: [], designations: [], genders: [], statuses: [], verification_statuses: [] },
  "dtmgp.api.v1.hr.list_lga_companies": ["Makurdi Local Government Area", "Gboko Local Government Area"],
  "dtmgp.api.v1.people.list_employees": { items: [], total: 0 },
  "dtmgp.api.v1.hr.list_staffing_plans": { items: [] },
  "dtmgp.api.v1.hr.get_establishment_report": { positions: [] },
  "dtmgp.api.v1.people.get_establishment": [],
};
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  const key = Object.keys(API_RESPONSES).find((candidate) => path.includes(candidate));
  return Promise.resolve(key ? API_RESPONSES[key] : {});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args) }));

import { useSessionStore } from "@/stores/session";
import PeopleHrView from "./PeopleHrView.vue";

function activateSession() {
  const session = useSessionStore();
  session.activeLga = "Makurdi Local Government Area";
  return session;
}

describe("PeopleHrView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
    mockRouteParams = {};
  });

  it("loads the scoped dashboard on mount", async () => {
    activateSession();
    const wrapper = mount(PeopleHrView);
    await flushPromises();
    expect(wrapper.text()).toContain("People & HR");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_dashboard"));
  });

  it("hides the Payroll and Staff Audit tabs when the session lacks access", async () => {
    const session = activateSession();
    session.canViewPayroll = false;
    session.canViewStaffAudit = false;
    const wrapper = mount(PeopleHrView);
    await flushPromises();
    const labels = wrapper.findAll(".hr-tabs button").map((button) => button.text());
    expect(labels).not.toContain("Payroll");
    expect(labels).not.toContain("Staff Audit");
  });

  it("shows the Payroll and Staff Audit tabs when the session grants access", async () => {
    const session = activateSession();
    session.canViewPayroll = true;
    session.canViewStaffAudit = true;
    const wrapper = mount(PeopleHrView);
    await flushPromises();
    const labels = wrapper.findAll(".hr-tabs button").map((button) => button.text());
    expect(labels).toContain("Payroll");
    expect(labels).toContain("Staff Audit");
  });

  it("switches to the Establishment tab and loads staffing plans and positions on click", async () => {
    activateSession();
    const wrapper = mount(PeopleHrView);
    await flushPromises();
    apiRequest.mockClear();

    const establishmentTab = wrapper.findAll(".hr-tabs button").find((button) => button.text() === "Establishment");
    await establishmentTab?.trigger("click");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("list_staffing_plans"));
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_establishment_report"));
  });

  it("initializes the active tab from the HR workspace route section", async () => {
    mockRouteParams = { section: "establishment-control" };
    activateSession();
    const wrapper = mount(PeopleHrView);
    await flushPromises();

    const active = wrapper.find(".hr-tabs button.active");
    expect(active.text()).toBe("Establishment");
  });
});
