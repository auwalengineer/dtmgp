import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ReportActions from "./ReportActions.vue";

describe("ReportActions", () => {
  it("disables export when a report has no rows", () => {
    const wrapper = mount(ReportActions, { props: { reportId: "hr.staff-strength", title: "Staff Strength", columns: ["Department", "Staff"], rows: [] } });
    expect(wrapper.get("button[disabled]").text()).toContain("Export CSV");
  });

  it("opens print from the report toolbar", async () => {
    const print = vi.spyOn(window, "print").mockImplementation(() => undefined);
    const wrapper = mount(ReportActions, { props: { reportId: "hr.staff-strength", title: "Staff Strength", columns: ["Department", "Staff"], rows: [["Finance", 2]] } });
    await wrapper.get("button").trigger("click");
    expect(print).toHaveBeenCalledOnce();
  });
});
