import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import RejectionReasonDialog from "./RejectionReasonDialog.vue";

describe("RejectionReasonDialog", () => {
  it("does not emit confirm with a blank reason", async () => {
    const wrapper = mount(RejectionReasonDialog, { props: { open: true, title: "Reject application" } });
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("confirm")).toBeFalsy();
  });

  it("emits confirm with the trimmed reason", async () => {
    const wrapper = mount(RejectionReasonDialog, { props: { open: true, title: "Reject application" } });
    await wrapper.find("textarea").setValue("  Missing supporting documents  ");
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("confirm")?.[0]).toEqual(["Missing supporting documents"]);
  });

  it("clears the reason when reopened", async () => {
    const wrapper = mount(RejectionReasonDialog, { props: { open: true, title: "Reject application" } });
    await wrapper.find("textarea").setValue("First reason");
    await wrapper.setProps({ open: false });
    await wrapper.setProps({ open: true });
    expect((wrapper.find("textarea").element as HTMLTextAreaElement).value).toBe("");
  });
});
