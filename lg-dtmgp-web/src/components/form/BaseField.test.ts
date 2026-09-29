import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import BaseField from "./BaseField.vue";

describe("BaseField", () => {
  it("shows a required marker and renders the slotted control", () => {
    const wrapper = mount(BaseField, { props: { label: "Title", required: true }, slots: { default: "<input />" } });
    expect(wrapper.text()).toContain("Title");
    expect(wrapper.find(".field-required").exists()).toBe(true);
    expect(wrapper.find("input").exists()).toBe(true);
  });

  it("shows the error message instead of the hint when both are set", () => {
    const wrapper = mount(BaseField, { props: { label: "Title", error: "Title is required", hint: "Keep it short" } });
    expect(wrapper.find(".field-error").text()).toBe("Title is required");
    expect(wrapper.find(".field-hint").exists()).toBe(false);
  });

  it("shows the hint when there is no error", () => {
    const wrapper = mount(BaseField, { props: { label: "Title", hint: "Keep it short" } });
    expect(wrapper.find(".field-hint").text()).toBe("Keep it short");
  });

  it("applies the full-field class when fullWidth is set", () => {
    const wrapper = mount(BaseField, { props: { label: "Title", fullWidth: true } });
    expect(wrapper.classes()).toContain("full-field");
  });
});
