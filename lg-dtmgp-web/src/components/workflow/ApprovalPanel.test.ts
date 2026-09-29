import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ApprovalPanel from "./ApprovalPanel.vue";

describe("ApprovalPanel", () => {
  it("fires a transition immediately for a plain option", async () => {
    const wrapper = mount(ApprovalPanel, { props: { options: [{ label: "Mark completed", target: "Completed" }] } });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("transition")?.[0]).toEqual(["Completed"]);
  });

  it("requires confirmation before firing a confirm-gated option", async () => {
    const wrapper = mount(ApprovalPanel, { props: { options: [{ label: "Cancel", target: "Cancelled", confirm: "This cannot be undone.", danger: true }] } });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("transition")).toBeFalsy();

    const confirmButton = wrapper.findAll(".user-modal button").find((b) => b.text() === "Confirm");
    await confirmButton?.trigger("click");
    expect(wrapper.emitted("transition")?.[0]).toEqual(["Cancelled"]);
  });

  it("requires a written reason before firing a reason-gated option", async () => {
    const wrapper = mount(ApprovalPanel, { props: { options: [{ label: "Reject", target: "Rejected", requiresReason: true }] } });
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("transition")).toBeFalsy();

    await wrapper.find("textarea").setValue("Does not meet eligibility criteria");
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("transition")?.[0]).toEqual(["Rejected", "Does not meet eligibility criteria"]);
  });
});
