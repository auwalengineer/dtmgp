import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import { useSessionStore } from "@/stores/session";
import MyProfileView from "./MyProfileView.vue";

describe("MyProfileView", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("renders the signed-in user's own details, not another user's", () => {
    const session = useSessionStore();
    session.user = { email: "treasurer@makurdi.gov.ng", name: "Amina Bello", role: "Treasurer" };
    session.activeLga = "Makurdi Local Government Area";
    session.allowedLgas = ["Makurdi Local Government Area"];

    const wrapper = mount(MyProfileView);
    expect(wrapper.text()).toContain("Amina Bello");
    expect(wrapper.text()).toContain("treasurer@makurdi.gov.ng");
    expect(wrapper.text()).toContain("Treasurer");
    expect(wrapper.text()).toContain("Makurdi Local Government Area");
  });

  it("shows every authorized LGA only for a multi-LGA (state) user", () => {
    const session = useSessionStore();
    session.user = { email: "admin@benue.gov.ng", name: "State Admin", role: "State Administrator" };
    session.allowedLgas = ["Makurdi Local Government Area", "Gboko Local Government Area"];

    const wrapper = mount(MyProfileView);
    expect(wrapper.text()).toContain("All authorized LGAs");
    expect(wrapper.text()).toContain("Gboko Local Government Area");
  });
});
