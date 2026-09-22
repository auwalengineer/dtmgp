import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
const routerPush = vi.fn();
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }), useRouter: () => ({ push: routerPush }) }));

const DASHBOARD = {
  scope: "Makurdi Local Government Area", can_manage: true,
  correspondence: { draft: 1, registered: 2, dispatched: 0, overdue_assigned: 0 },
  departments: 3, meetings_scheduled: 1, resolutions_proposed: 1, actions_overdue: 0, returns_overdue: 0, compliance_non_compliant: 0, pending_approvals: 2,
};
const FORM_OPTIONS = {
  departments: ["Registry"], users: [{ name: "secretary@example.com", full_name: "LGA Secretary" }],
  meetings: [{ name: "CM-MKD-2026-00001", title: "Sept Council Meeting" }],
  resolutions: [{ name: "RES-MKD-2026-00001", title: "Approve market renovation" }],
  return_types: [{ name: "Monthly Financial Return", return_name: "Monthly Financial Return", frequency: "Monthly" }],
  compliance_requirements: [{ name: "Council Meeting Minutes Filing", requirement_name: "Council Meeting Minutes Filing", frequency: "Monthly" }],
  roles: ["LGA Chairman", "LGA Secretary"],
};
const API_RESPONSES: Record<string, unknown> = {
  "dtmgp.api.v1.governance.get_dashboard": DASHBOARD,
  "dtmgp.api.v1.governance.get_form_options": FORM_OPTIONS,
  "dtmgp.api.v1.governance.list_departments": [{ name: "Registry", department_name: "Registry", company: "Makurdi Local Government Area", disabled: 0, is_group: 0, parent_department: null }],
  "dtmgp.api.v1.governance.save_record": { name: "COR-MKD-2026-00002", doctype: "DTMGP Correspondence", status: "Draft" },
  "dtmgp.api.v1.governance.get_reports": { meetings: { scheduled: 1, held: 2, cancelled: 0, postponed: 0 }, resolutions: { proposed: 1, adopted: 3, rejected: 0 }, resolution_actions: { pending: 1, completed: 2, overdue: 0 }, statutory_returns: { submitted: 4, overdue: 1 }, compliance: { verified: 2, non_compliant: 1, pending: 0 } },
  "dtmgp.api.v1.governance.get_approvals_inbox": [{ doctype: "DTMGP Statutory Return", name: "RET-MKD-2026-00001", title: "2026-Q3", company: "Makurdi Local Government Area", status: "Submitted" }],
};
const LIST_RECORDS_FIXTURES: Record<string, unknown> = {
  "DTMGP Correspondence": { name: "COR-MKD-2026-00001", correspondence_type: "Incoming", subject: "State circular", correspondent: "Governor's Office", department: null, correspondence_date: "2026-09-19", priority: "Routine", status: "Draft", assigned_to: null, due_date: null },
  "DTMGP Meeting": { name: "CM-MKD-2026-00001", meeting_type: "Council", title: "Sept Council Meeting", meeting_date: "2026-09-21", venue: "Council Hall", status: "Scheduled", minutes_finalized: 0 },
};
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("list_records")) {
    const doctype = new URL(path, "http://localhost").searchParams.get("doctype") || "";
    const fixture = LIST_RECORDS_FIXTURES[doctype];
    return Promise.resolve({ items: fixture ? [fixture] : [], total: fixture ? 1 : 0 });
  }
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
    routerPush.mockClear();
    mockRouteParams = {};
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

  it("filters correspondence and switches the active tab based on the workspace route section/item", async () => {
    mockRouteParams = { section: "correspondence", item: "assigned-correspondence" };
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("assigned_to=secretary%40example.com"));
    expect(wrapper.text()).toContain("Assigned Correspondence");

    mockRouteParams = { section: "departments-units" };
    const departmentsWrapper = mount(GovernanceView);
    await flushPromises();
    expect(departmentsWrapper.find(".hr-tabs button.active").text()).toBe("Departments & Units");
  });

  it("shows a real Meetings workspace instead of a placeholder", async () => {
    mockRouteParams = { section: "meetings" };
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();

    expect(wrapper.find(".hr-tabs button.active").text()).toBe("Meetings");
    expect(wrapper.text()).toContain("Sept Council Meeting");
    expect(wrapper.text()).not.toContain("not built yet");
  });

  it("routes the Approvals section to the cross-cutting inbox and lets a reviewer act on an item", async () => {
    mockRouteParams = { section: "approvals" };
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_approvals_inbox"));
    expect(wrapper.text()).toContain("Statutory Return");

    const reviewButton = wrapper.findAll("button").find((button) => button.text() === "State Review");
    await reviewButton?.trigger("click");
    await flushPromises();
    expect(apiRequest).toHaveBeenCalledWith("/api/method/dtmgp.api.v1.governance.transition_record", expect.objectContaining({ method: "POST", body: JSON.stringify({ doctype: "DTMGP Statutory Return", name: "RET-MKD-2026-00001", target_status: "State Reviewed" }) }));
  });

  it("shows the Reports tab's aggregate summary", async () => {
    mockRouteParams = { section: "reports" };
    activateSession();
    const wrapper = mount(GovernanceView);
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_reports"));
    expect(wrapper.text()).toContain("adopted");
  });
});
