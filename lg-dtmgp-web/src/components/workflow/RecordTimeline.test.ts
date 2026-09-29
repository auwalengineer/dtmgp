import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

const apiRequest = vi.fn();
vi.mock("@/services/api", () => ({ apiRequest: (...args: unknown[]) => apiRequest(...args) }));

import RecordTimeline from "./RecordTimeline.vue";

describe("RecordTimeline", () => {
  it("requests this record's own timeline and renders its events", async () => {
    apiRequest.mockResolvedValueOnce({ items: [
      { name: "AE-1", occurred_at: "2026-09-16 10:00:00", event_type: "workflow_transition", outcome: "Success", actor: "treasurer@makurdi.gov.ng", summary: "Contract advanced to Active" },
    ] });
    const wrapper = mount(RecordTimeline, { props: { doctype: "DTMGP Contract", name: "CON-MKD-2026-00001" } });
    await flushPromises();

    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("dtmgp.api.v1.records.get_record_timeline"));
    expect(apiRequest).toHaveBeenCalledWith(expect.stringContaining("doctype=DTMGP%20Contract"));
    expect(wrapper.text()).toContain("Contract advanced to Active");
  });

  it("shows an empty state when there is no history yet", async () => {
    apiRequest.mockResolvedValueOnce({ items: [] });
    const wrapper = mount(RecordTimeline, { props: { doctype: "DTMGP Contract", name: "CON-MKD-2026-00002" } });
    await flushPromises();
    expect(wrapper.text()).toContain("No recorded history for this record yet.");
  });

  it("shows an error message when the request fails", async () => {
    apiRequest.mockRejectedValueOnce(new Error("Unable to load history"));
    const wrapper = mount(RecordTimeline, { props: { doctype: "DTMGP Contract", name: "CON-MKD-2026-00003" } });
    await flushPromises();
    expect(wrapper.find(".login-error").text()).toBe("Unable to load history");
  });
});
