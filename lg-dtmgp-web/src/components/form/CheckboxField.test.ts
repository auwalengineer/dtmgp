import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import CheckboxField from "./CheckboxField.vue";

describe("CheckboxField", () => {
  it("reflects a Frappe-style 1/0 model as checked state", () => {
    const checked = mount(CheckboxField, { props: { label: "Primary contact", modelValue: 1 } });
    expect((checked.find("input").element as HTMLInputElement).checked).toBe(true);
    const unchecked = mount(CheckboxField, { props: { label: "Primary contact", modelValue: 0 } });
    expect((unchecked.find("input").element as HTMLInputElement).checked).toBe(false);
  });

  it("emits 1 when checked and 0 when unchecked", async () => {
    const wrapper = mount(CheckboxField, { props: { label: "Primary contact", modelValue: 0 } });
    await wrapper.find("input").setValue(true);
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([1]);
  });
});
