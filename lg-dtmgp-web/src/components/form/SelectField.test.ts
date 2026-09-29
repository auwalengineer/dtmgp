import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import SelectField from "./SelectField.vue";

const OPTIONS = [
  { value: "State", label: "State" },
  { value: "Federal", label: "Federal" },
];

describe("SelectField", () => {
  it("renders every option plus a disabled placeholder", () => {
    const wrapper = mount(SelectField, { props: { label: "Funding source", options: OPTIONS, placeholder: "Select source" } });
    const options = wrapper.findAll("option");
    expect(options).toHaveLength(3);
    expect(options[0].attributes("disabled")).toBeDefined();
    expect(options[0].text()).toBe("Select source");
    expect(options.slice(1).map((o) => o.text())).toEqual(["State", "Federal"]);
  });

  it("emits the selected option's value", async () => {
    const wrapper = mount(SelectField, { props: { label: "Funding source", options: OPTIONS, modelValue: "" } });
    await wrapper.find("select").setValue("Federal");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["Federal"]);
  });

  it("omits the placeholder option when none is given", () => {
    const wrapper = mount(SelectField, { props: { label: "Funding source", options: OPTIONS } });
    expect(wrapper.findAll("option")).toHaveLength(2);
  });
});
