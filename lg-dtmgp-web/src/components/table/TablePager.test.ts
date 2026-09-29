import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import TablePager from "./TablePager.vue";

describe("TablePager", () => {
  it("shows the count and current page", () => {
    const wrapper = mount(TablePager, { props: { page: 2, pageSize: 20, total: 45, itemCount: 20 } });
    expect(wrapper.text()).toContain("Showing 20 of 45");
    expect(wrapper.find("button.current").text()).toBe("2");
  });

  it("disables Previous on the first page and Next on the last page", () => {
    const first = mount(TablePager, { props: { page: 1, pageSize: 20, total: 45, itemCount: 20 } });
    expect(first.findAll("button")[0].attributes("disabled")).toBeDefined();
    expect(first.findAll("button")[2].attributes("disabled")).toBeUndefined();

    const last = mount(TablePager, { props: { page: 3, pageSize: 20, total: 45, itemCount: 5 } });
    expect(last.findAll("button")[0].attributes("disabled")).toBeUndefined();
    expect(last.findAll("button")[2].attributes("disabled")).toBeDefined();
  });

  it("emits change-page with the right delta", async () => {
    const wrapper = mount(TablePager, { props: { page: 2, pageSize: 20, total: 45, itemCount: 20 } });
    await wrapper.findAll("button")[2].trigger("click");
    expect(wrapper.emitted("change-page")?.[0]).toEqual([1]);
    await wrapper.findAll("button")[0].trigger("click");
    expect(wrapper.emitted("change-page")?.[1]).toEqual([-1]);
  });
});
