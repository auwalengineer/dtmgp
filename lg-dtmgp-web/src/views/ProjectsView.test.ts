import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const DASHBOARD = { scope: "Makurdi Local Government Area", lga_count: 1, projects: { total: 3, ongoing: 2, completed: 1, delayed: 1, suspended: 0, abandoned: 0 }, inspections: { open: 1, exceptions: 0 }, assets: { registered: 4 }, fleet: { vehicles: 2, insurance_due: 1 }, can_manage: true };
const OPTIONS = { employees: [], locations: [], asset_categories: [], items: [], open_projects: [] };
const PROJECTS = { items: [{ name: "PROJ-1", project_name: "Rural Road Rehabilitation", company: "Makurdi Local Government Area", status: "Open", percent_complete: 40, expected_start_date: "2026-01-01", expected_end_date: "2026-12-31", dtmgp_location: null, dtmgp_funding_source: null, department: null, priority: "Medium", creation: "2026-01-01 00:00:00" }] };
const API_RESPONSES: Record<string, unknown> = {
  "dtmgp.api.v1.projects.get_dashboard": DASHBOARD,
  "dtmgp.api.v1.projects.get_form_options": OPTIONS,
  "dtmgp.api.v1.projects.list_projects": PROJECTS,
  "dtmgp.api.v1.projects.list_tasks": { items: [] },
};
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("list_records")) return Promise.resolve({ items: [] });
  const key = Object.keys(API_RESPONSES).find((candidate) => path.includes(candidate));
  return Promise.resolve(key ? API_RESPONSES[key] : {});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args), uploadFile: vi.fn() }));

import { useSessionStore } from "@/stores/session";
import ProjectsView from "./ProjectsView.vue";

function activateSession() {
  const session = useSessionStore();
  session.activeLga = "Makurdi Local Government Area";
  return session;
}

describe("ProjectsView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
    mockRouteParams = {};
  });

  it("loads the scoped dashboard and defaults to Projects", async () => {
    activateSession();
    const wrapper = mount(ProjectsView);
    await flushPromises();
    expect(wrapper.text()).toContain("Projects, Assets & Field Monitoring");
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Projects");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_dashboard"));
  });

  it("renders all 9 nav sections as top-level tabs", async () => {
    activateSession();
    const wrapper = mount(ProjectsView);
    await flushPromises();
    const labels = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").map((button) => button.text());
    expect(labels).toEqual(["Projects", "Project Planning", "Contractors", "Field Monitoring", "Progress Monitoring", "Assets", "Fleet Management", "Maps", "Reports"]);
  });

  it("shows real project records from the register, not a placeholder card", async () => {
    activateSession();
    const wrapper = mount(ProjectsView);
    await flushPromises();
    expect(wrapper.text()).toContain("Rural Road Rehabilitation");
  });

  it("initializes the active section from the route and loads its data", async () => {
    mockRouteParams = { section: "assets" };
    activateSession();
    const wrapper = mount(ProjectsView);
    await flushPromises();
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Assets");
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("list_records"));
  });

  it("shows a distinct planned-content card for a no-backend item like Project Proposals", async () => {
    activateSession();
    const wrapper = mount(ProjectsView);
    await flushPromises();

    const tab = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").find((button) => button.text() === "Project Planning");
    await tab?.trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("isn't modeled yet -- ERPNext's Project doctype only tracks a project once it exists");
  });
});
