import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

const API_RESPONSES: Record<string, unknown> = {
  "dtmgp.api.v1.governance.get_dashboard": { scope: "Makurdi Local Government Area", can_manage: true, correspondence: { draft: 1, registered: 2, dispatched: 0, overdue_assigned: 0 }, departments: 3 },
  "dtmgp.api.v1.governance.get_form_options": { departments: ["Registry"], users: [{ name: "secretary@example.com", full_name: "LGA Secretary" }] },
  "dtmgp.api.v1.governance.list_records": { items: [{ name: "COR-MKD-2026-00001", correspondence_type: "Incoming", subject: "State circular", correspondent: "Governor's Office", department: null, correspondence_date: "2026-09-19", priority: "Routine", status: "Draft", assigned_to: null, due_date: null }], total: 1 },
  "dtmgp.api.v1.governance.list_departments": [{ name: "Registry", department_name: "Registry", company: "Makurdi Local Government Area", disabled: 0, is_group: 0, parent_department: null }],
  "dtmgp.api.v1.governance.save_record": { name: "COR-MKD-2026-00002", doctype: "DTMGP Correspondence", status: "Draft" },
};
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  const key = Object.keys(API_RESPONSES).find((candidate) => path.includes(candidate));
  return Promise.resolve(key ? API_RESPONSES[key] : {});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args) }));

import { useSessionStore } from "@/stores/session";
import GovernanceView from "./GovernanceView.vue";

function activateSession() {
  const session = useSessionStore();
  session.activeLga = "Makurdi Local Government Area";
  session.user.email = "secretary@example.com";
  return session;
}

describe("GovernanceView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
  });

  it("loads the scoped dashboard on mount", async () => {
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();
    expect(wrapper.text()).toContain("Administration & Governance");
    expect(wrapper.text()).toContain("State circular");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_dashboard"));
  });

  it("switches to the Departments & Units tab and loads departments", async () => {
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();
    apiRequest.mockClear();

    const tab = wrapper.findAll(".hr-tabs button").find((button) => button.text() === "Departments & Units");
    await tab?.trigger("click");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("list_departments"));
    expect(wrapper.text()).toContain("Registry");
  });

  it("submits a new correspondence record", async () => {
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();

    await wrapper.find(".primary-action").trigger("click");
    await wrapper.find(".finance-modal input[required]").setValue("New circular from state house");
    await wrapper.find(".finance-modal").trigger("submit");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith("/api/method/dtmgp.api.v1.governance.save_record", expect.objectContaining({ method: "POST" }));
  });
});
