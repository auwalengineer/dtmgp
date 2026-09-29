import { mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";
import { defineComponent } from "vue";

import { recordDirective } from "./record";

afterEach(() => vi.restoreAllMocks());

describe("record directive", () => {
  it("opens a record from a row click but preserves action buttons", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ message: {} }), { status: 200 }));
    const wrapper = mount(defineComponent({
      template: `<table><tbody><tr v-record="{ doctype: 'Employee', name: 'EMP-001' }"><td>Staff</td><td><button>Approve</button></td></tr></tbody></table>`,
    }), { global: { directives: { record: recordDirective } } });

    await wrapper.find("button").trigger("click");
    expect(fetchMock).not.toHaveBeenCalled();
    await wrapper.find("tr").trigger("click");
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("doctype=Employee&name=EMP-001"), expect.anything());
  });

  it("supports keyboard activation", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ message: {} }), { status: 200 }));
    const wrapper = mount(defineComponent({
      template: `<table><tbody><tr v-record="{ doctype: 'Project', name: 'PROJ-001' }"><td>Road</td></tr></tbody></table>`,
    }), { global: { directives: { record: recordDirective } } });

    expect(wrapper.find("tr").attributes("tabindex")).toBe("0");
    await wrapper.find("tr").trigger("keydown", { key: "Enter" });
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
