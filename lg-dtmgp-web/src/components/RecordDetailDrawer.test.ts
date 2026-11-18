import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it, vi } from "vitest";

import { closeRecordDetails, openRecordDetails } from "@/services/recordDetails";
import { apiRequest } from "@/services/api";

import EmployeeAvatar from "@/views/hr/EmployeeAvatar.vue";
import RecordDetailDrawer from "./RecordDetailDrawer.vue";

vi.mock("@/services/api", () => ({ apiRequest: vi.fn() }));

const RECORD = {
  doctype: "Employee", doctype_label: "Employee", name: "HR-0001", title: "Amina Bello", status: "Active",
  modified: "18-11-2026", sections: [{ label: "Details", fields: [{ label: "LGA", value: "Makurdi Local Government Area", type: "Link" }] }],
};

function stubRequests(image: string | null) {
  vi.mocked(apiRequest).mockImplementation((path: string) =>
    Promise.resolve(path.includes("get_record_timeline") ? { items: [] } : { ...RECORD, image }) as never,
  );
}

afterEach(() => { closeRecordDetails(); document.body.innerHTML = ""; vi.mocked(apiRequest).mockReset(); });

describe("RecordDetailDrawer photo", () => {
  it("shows the employee photo and expands it to a full-size preview", async () => {
    stubRequests("/private/files/amina.jpg");
    mount(RecordDetailDrawer, { attachTo: document.body });
    await openRecordDetails({ doctype: "Employee", name: "HR-0001" });
    await flushPromises();

    const thumb = document.querySelector<HTMLButtonElement>(".record-detail-photo");
    expect(thumb?.querySelector("img")?.getAttribute("src")).toBe("/private/files/amina.jpg");
    thumb?.click();
    await flushPromises();

    const preview = document.querySelector(".image-lightbox");
    expect(preview?.querySelector("img")?.getAttribute("alt")).toBe("Photo of Amina Bello");
    expect(preview?.querySelector("a")?.getAttribute("href")).toBe("/private/files/amina.jpg");

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await flushPromises();
    expect(document.querySelector(".image-lightbox")).toBeNull();
    // Esc closed only the preview; the drawer stays open.
    expect(document.querySelector(".record-detail-drawer")).not.toBeNull();
  });

  it("shows no photo block when the record has no image", async () => {
    stubRequests(null);
    mount(RecordDetailDrawer, { attachTo: document.body });
    await openRecordDetails({ doctype: "Employee", name: "HR-0001" });
    await flushPromises();
    expect(document.querySelector(".record-detail-drawer")).not.toBeNull();
    expect(document.querySelector(".record-detail-photo")).toBeNull();
  });
});

describe("EmployeeAvatar", () => {
  it("expands a large photo when expandable, and stays a plain avatar otherwise", async () => {
    const expandable = mount(EmployeeAvatar, { props: { name: "Amina Bello", image: "/files/a.png", large: true, expandable: true }, attachTo: document.body });
    await expandable.get("button").trigger("click");
    expect(document.querySelector(".image-lightbox img")?.getAttribute("src")).toBe("/files/a.png");
    expandable.unmount();

    const plain = mount(EmployeeAvatar, { props: { name: "Amina Bello", image: "/files/a.png" } });
    expect(plain.find("button").exists()).toBe(false);
    const initialsOnly = mount(EmployeeAvatar, { props: { name: "Amina Bello", image: null, expandable: true } });
    expect(initialsOnly.find("button").exists()).toBe(false);
  });
});
