import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import ReportActions from "./ReportActions.vue";

describe("ReportActions", () => {
  it("disables export when a report has no rows", () => {
    const wrapper = mount(ReportActions, { props: { reportId: "hr.staff-strength", title: "Staff Strength", columns: ["Department", "Staff"], rows: [] } });
    expect(wrapper.get("button[disabled]").text()).toContain("Export CSV");
  });

  it("opens a dedicated print document from the report toolbar", async () => {
    const write = vi.fn();
    const close = vi.fn();
    const open = vi.spyOn(window, "open").mockReturnValue({ document: { write, close } } as unknown as Window);
    const wrapper = mount(ReportActions, { props: { reportId: "hr.staff-strength", title: "Staff Strength", columns: ["Department", "Staff"], rows: [["Finance", 2]] } });
    await wrapper.get("button").trigger("click");
    expect(open).toHaveBeenCalledOnce();
    expect(write.mock.calls[0][0]).toContain("Benue State Local Government Administration");
    expect(write.mock.calls[0][0]).toContain("Staff Strength");
  });
});
