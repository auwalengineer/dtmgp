import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

const DASHBOARD = { active_institutions: 4, reigning_rulers: 3, vacant_stools: 1, pending_recognition: 2, open_petitions: 1, can_manage: true };
const apiRequest = vi.fn((path: string, _options?: RequestInit) => {
  if (path.includes("get_dashboard")) return Promise.resolve(DASHBOARD);
  if (path.includes("list_records") || path.includes("get_traditional_reports")) return Promise.resolve({ items: [] });
  return Promise.resolve({});
});
vi.mock("@/services/api", () => ({ apiRequest: (...args: [string, RequestInit?]) => apiRequest(...args) }));

import { useSessionStore } from "@/stores/session";
import TraditionalAffairsView from "./TraditionalAffairsView.vue";

describe("TraditionalAffairsView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiRequest.mockClear();
    mockRouteParams = {};
    const session = useSessionStore();
    session.activeLga = "Makurdi Local Government Area";
  });

  it("loads the scoped dashboard and defaults to Traditional Institutions", async () => {
    const wrapper = mount(TraditionalAffairsView);
    await flushPromises();
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("get_dashboard"));
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Traditional Institutions");
    expect(wrapper.text()).toContain("Reigning rulers");
    expect(wrapper.text()).toContain("Institution register");
  });

  it("renders all 8 nav sections as top-level tabs", async () => {
    const wrapper = mount(TraditionalAffairsView);
    await flushPromises();
    const labels = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").map((button) => button.text());
    expect(labels).toEqual(["Traditional Institutions", "Traditional Rulers", "Appointments", "Succession", "Recognition & Certification", "Petitions & Disputes", "Allowances & Entitlements", "Reports"]);
  });

  it("initializes the active section from the route and shows its item tabs", async () => {
    mockRouteParams = { section: "traditional-rulers" };
    const wrapper = mount(TraditionalAffairsView);
    await flushPromises();
    expect(wrapper.find(".hr-tabs:not(.hr-item-tabs) button.active").text()).toBe("Traditional Rulers");
    const itemLabels = wrapper.findAll(".hr-item-tabs button").map((button) => button.text());
    expect(itemLabels).toEqual(["Rulers Register", "Current Rulers", "Former Rulers", "Vacant Stools", "Ruler Profiles"]);
  });

  it("switches to Petitions & Disputes and calls the real petitions API", async () => {
    const wrapper = mount(TraditionalAffairsView);
    await flushPromises();
    apiRequest.mockClear();

    const petitionsTab = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").find((button) => button.text() === "Petitions & Disputes");
    await petitionsTab?.trigger("click");
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("DTMGP%20Chieftaincy%20Petition"));
    expect(wrapper.text()).toContain("Hearings");
  });
});
