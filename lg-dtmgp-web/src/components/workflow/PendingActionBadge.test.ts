import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import PendingActionBadge from "./PendingActionBadge.vue";

describe("PendingActionBadge", () => {
  it("falls back to a plain dot when there is no count", () => {
    const wrapper = mount(PendingActionBadge);
    expect(wrapper.find(".notification-dot").exists()).toBe(true);
    expect(wrapper.find(".pending-badge").exists()).toBe(false);
  });

  it("shows the count when there is one", () => {
    const wrapper = mount(PendingActionBadge, { props: { count: 7 } });
    expect(wrapper.find(".pending-badge").text()).toBe("7");
  });

  it("caps the displayed count at 99+", () => {
    const wrapper = mount(PendingActionBadge, { props: { count: 140 } });
    expect(wrapper.find(".pending-badge").text()).toBe("99+");
  });
});
