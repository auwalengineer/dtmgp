import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

let mockRouteParams: Record<string, string> = {};
vi.mock("vue-router", () => ({ useRoute: () => ({ params: mockRouteParams }) }));

import { useSessionStore } from "@/stores/session";
import TraditionalAffairsView from "./TraditionalAffairsView.vue";

describe("TraditionalAffairsView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockRouteParams = {};
    const session = useSessionStore();
    session.activeLga = "Makurdi Local Government Area";
  });

  it("defaults to Traditional Institutions and explains the domain is not yet operational", () => {
    const wrapper = mount(TraditionalAffairsView);
    expect(wrapper.find(".hr-tabs button.active").text()).toBe("Traditional Institutions");
    expect(wrapper.text()).toContain("isn't operational yet");
    expect(wrapper.text()).toContain("Institution register");
  });

  it("renders all 8 nav sections as top-level tabs", () => {
    const wrapper = mount(TraditionalAffairsView);
    const labels = wrapper.findAll(".hr-tabs:not(.hr-item-tabs) button").map((button) => button.text());
    expect(labels).toEqual(["Traditional Institutions", "Traditional Rulers", "Appointments", "Succession", "Recognition & Certification", "Petitions & Disputes", "Allowances & Entitlements", "Reports"]);
  });

  it("initializes the active section from the route and shows its item tabs", () => {
    mockRouteParams = { section: "traditional-rulers" };
    const wrapper = mount(TraditionalAffairsView);
    expect(wrapper.find(".hr-tabs button.active").text()).toBe("Traditional Rulers");
    const itemLabels = wrapper.findAll(".hr-item-tabs button").map((button) => button.text());
    expect(itemLabels).toEqual(["Rulers Register", "Current Rulers", "Former Rulers", "Vacant Stools", "Ruler Profiles"]);
  });

  it("shows a distinct planned-content card per item, not a generic placeholder", async () => {
    const wrapper = mount(TraditionalAffairsView);
    const petitionsTab = wrapper.findAll(".hr-tabs button").find((button) => button.text() === "Petitions & Disputes");
    await petitionsTab?.trigger("click");
    const hearingsItem = wrapper.findAll(".hr-item-tabs button").find((button) => button.text() === "Hearings");
    await hearingsItem?.trigger("click");
    expect(wrapper.text()).toContain("Scheduling and records of dispute hearings aren't available yet.");
  });
});
