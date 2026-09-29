import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ConfirmDialog from "./ConfirmDialog.vue";

describe("ConfirmDialog", () => {
  it("renders nothing when closed", () => {
    const wrapper = mount(ConfirmDialog, { props: { open: false, title: "Cancel project", message: "Are you sure?" } });
    expect(wrapper.find(".modal-backdrop").exists()).toBe(false);
  });

  it("emits confirm and cancel", async () => {
    const wrapper = mount(ConfirmDialog, { props: { open: true, title: "Cancel project", message: "Are you sure?" } });
    const buttons = wrapper.findAll("button");
    expect(buttons[1].text()).toBe("Confirm");
    await buttons[1].trigger("click");
    expect(wrapper.emitted("confirm")).toBeTruthy();
    await buttons[0].trigger("click");
    expect(wrapper.emitted("cancel")).toBeTruthy();
  });

  it("disables the confirm button while saving", () => {
    const wrapper = mount(ConfirmDialog, { props: { open: true, title: "t", message: "m", saving: true } });
    expect(wrapper.findAll("button")[1].attributes("disabled")).toBeDefined();
    expect(wrapper.findAll("button")[1].text()).toBe("Working...");
  });
});
