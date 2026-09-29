import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import NumberField from "./NumberField.vue";

describe("NumberField", () => {
  it("emits a numeric value, not a string", async () => {
    const wrapper = mount(NumberField, { props: { label: "Amount", modelValue: 0 } });
    await wrapper.find("input").setValue("500000");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([500000]);
  });

  it("passes min/max/step through to the native input", () => {
    const wrapper = mount(NumberField, { props: { label: "Amount", min: 0, max: 100, step: 0.01 } });
    const input = wrapper.find("input");
    expect(input.attributes("min")).toBe("0");
    expect(input.attributes("max")).toBe("100");
    expect(input.attributes("step")).toBe("0.01");
  });
});
