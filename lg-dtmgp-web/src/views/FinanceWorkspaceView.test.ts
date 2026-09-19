import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const DASHBOARD = { scope: "Makurdi Local Government Area", lga_count: 1, revenue: { assessed: 500000, collected: 300000, outstanding: 200000 }, procurement: { planned: 2, active: 1, pending_approval: 1 }, payments: { pending: 100000, paid: 50000 }, audit: { open_queries: 1, overdue_queries: 0 }, can_manage: true };
const OPTIONS = { departments: [], accounts: [], cost_centers: [], fiscal_years: [], revenue_heads: [], procurement_plans: [] };
const API_RESPONSES: Record<string, unknown> = {
  "dtmgp.api.v1.finance.get_dashboard": DASHBOARD,
  "dtmgp.api.v1.finance.get_form_options": OPTIONS,
};
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("list_records")) return Promise.resolve({ items: [] });
  const key = Object.keys(API_RESPONSES).find((candidate) => path.includes(candidate));
  return Promise.resolve(key ? API_RESPONSES[key] : {});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args) }));

import { useSessionStore } from "@/stores/session";
import FinanceWorkspaceView from "./FinanceWorkspaceView.vue";

function activateSession() {
  const session = useSessionStore();
  session.activeLga = "Makurdi Local Government Area";
  return session;
}

describe("FinanceWorkspaceView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
    mockRouteParams = {};
  });

  it("loads the scoped dashboard and defaults to Budget", async () => {
    activateSession();
    const wrapper = mount(FinanceWorkspaceView);
    await flushPromises();
    expect(wrapper.text()).toContain("Finance, Revenue & Procurement");
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Budget");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_dashboard"));
  });

  it("initializes the active section from the route", async () => {
    mockRouteParams = { section: "audit-control" };
    activateSession();
    const wrapper = mount(FinanceWorkspaceView);
    await flushPromises();
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Audit & Control");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("list_records"));
  });

  it("switches to Procurement and loads both plans and cases", async () => {
    activateSession();
    const wrapper = mount(FinanceWorkspaceView);
    await flushPromises();
    apiRequest.mockClear();

    const tab = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").find((button) => button.text() === "Procurement");
    await tab?.trigger("click");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("DTMGP%20Procurement%20Plan"));
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("DTMGP%20Procurement%20Case"));
  });

  it("shows a distinct planned-content card for a no-backend item like Chart of Accounts", async () => {
    activateSession();
    const wrapper = mount(FinanceWorkspaceView);
    await flushPromises();

    const tab = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").find((button) => button.text() === "Accounting");
    await tab?.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("ERPNext's Account list already exists");
  });
});
