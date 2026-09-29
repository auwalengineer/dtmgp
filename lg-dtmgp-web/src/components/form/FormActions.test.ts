import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FormActions from "./FormActions.vue";

describe("FormActions", () => {
  it("shows the default labels and enables the save button", () => {
    const wrapper = mount(FormActions);
    const buttons = wrapper.findAll("button");
    expect(buttons[0].text()).toBe("Cancel");
    expect(buttons[1].text()).toBe("Save");
    expect(buttons[1].attributes("disabled")).toBeUndefined();
  });

  it("shows the saving label and disables the save button while saving", () => {
    const wrapper = mount(FormActions, { props: { saving: true, saveLabel: "Save contract", savingLabel: "Saving contract..." } });
    expect(wrapper.findAll("button")[1].text()).toBe("Saving contract...");
    expect(wrapper.findAll("button")[1].attributes("disabled")).toBeDefined();
  });

  it("emits cancel and renders the error banner", () => {
    const wrapper = mount(FormActions, { props: { error: "Unable to save the record" } });
    expect(wrapper.find(".login-error").text()).toBe("Unable to save the record");
    wrapper.findAll("button")[0].trigger("click");
    expect(wrapper.emitted("cancel")).toBeTruthy();
  });
});
