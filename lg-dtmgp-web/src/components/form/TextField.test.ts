import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TextField from "./TextField.vue";

describe("TextField", () => {
  it("binds v-model both ways", async () => {
    const wrapper = mount(TextField, { props: { label: "Title", modelValue: "" } });
    await wrapper.find("input").setValue("Rural Road Rehabilitation");
    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual(["Rural Road Rehabilitation"]);
  });

  it("defaults to type=text and reflects an explicit type", () => {
    const text = mount(TextField, { props: { label: "Title" } });
    expect(text.find("input").attributes("type")).toBe("text");
    const email = mount(TextField, { props: { label: "Email", type: "email" } });
    expect(email.find("input").attributes("type")).toBe("email");
  });

  it("marks the input aria-invalid when an error is present", () => {
    const wrapper = mount(TextField, { props: { label: "Title", error: "Required" } });
    expect(wrapper.find("input").attributes("aria-invalid")).toBe("true");
  });
});
