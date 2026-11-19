import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const people = [
  { name: "HR-0001", employee_name: "Amina Bello", designation: "Officer", status: "Active", image: null },
  { name: "HR-0002", employee_name: "Tersoo Iorliam", designation: "Accountant", status: "Suspended", image: null },
];
const apiRequest = vi.fn((path: string) => {
  const term = new URLSearchParams(path.split("?")[1]).get("search")?.toLowerCase();
  const items = term ? people.filter((person) => person.employee_name.toLowerCase().includes(term) || person.name.toLowerCase().includes(term)) : people;
  return Promise.resolve({ items, total: term ? items.length : 57 });
});
vi.mock("@/services/api", () => ({ apiRequest: (path: string) => apiRequest(path) }));

import { useSessionStore } from "@/stores/session";
import EmployeePicker from "./EmployeePicker.vue";

function mountPicker() {
  setActivePinia(createPinia());
  useSessionStore().activeLga = "Makurdi Local Government Area";
  return mount(EmployeePicker, { props: { modelValue: "", "onUpdate:modelValue": (value: string) => wrapper.setProps({ modelValue: value }) }, attachTo: document.body });
}
let wrapper: ReturnType<typeof mountPicker>;
const lastQuery = () => new URLSearchParams(String(apiRequest.mock.calls.at(-1)?.[0]).split("?")[1]);

describe("EmployeePicker", () => {
  beforeEach(() => { vi.useFakeTimers(); apiRequest.mockClear(); wrapper = mountPicker(); });
  afterEach(() => { wrapper.unmount(); vi.useRealTimers(); });

  it("lists staff from the server for the active LGA when opened", async () => {
    await wrapper.get("input").trigger("focus");
    await flushPromises();
    expect(lastQuery().get("company")).toBe("Makurdi Local Government Area");
    expect(wrapper.findAll('[role="option"]')).toHaveLength(2);
    expect(wrapper.get("input").attributes("aria-expanded")).toBe("true");
    expect(wrapper.text()).toContain("Showing 2 of 57");
    expect(wrapper.text()).toContain("Suspended");
  });

  it("searches the server after typing stops", async () => {
    await wrapper.get("input").trigger("focus");
    await flushPromises();
    apiRequest.mockClear();
    await wrapper.get("input").setValue("ters");
    await wrapper.get("input").setValue("terso");
    expect(apiRequest).not.toHaveBeenCalled();
    vi.advanceTimersByTime(300);
    await flushPromises();
    expect(apiRequest).toHaveBeenCalledOnce();
    expect(lastQuery().get("search")).toBe("terso");
    expect(wrapper.findAll('[role="option"]').map((option) => option.text())).toEqual([expect.stringContaining("Tersoo Iorliam")]);
  });

  it("chooses with the keyboard and can be cleared", async () => {
    const input = wrapper.get("input");
    await input.trigger("focus");
    await flushPromises();
    await input.trigger("keydown", { key: "ArrowDown" });
    expect(input.attributes("aria-activedescendant")).toMatch(/option-1$/);
    await input.trigger("keydown", { key: "Enter" });
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual(["HR-0002"]);
    expect(input.attributes("aria-expanded")).toBe("false");
    expect(input.attributes("placeholder")).toBe("Tersoo Iorliam — HR-0002");

    await wrapper.get('button[aria-label="Clear selected staff member"]').trigger("click");
    expect(wrapper.emitted("update:modelValue")?.at(-1)).toEqual([""]);
  });

  it("says when nothing matches and closes on Escape", async () => {
    const input = wrapper.get("input");
    await input.trigger("focus");
    await input.setValue("zzz");
    vi.advanceTimersByTime(300);
    await flushPromises();
    expect(wrapper.text()).toContain("No staff match “zzz”");
    await input.trigger("keydown", { key: "Escape" });
    expect(input.attributes("aria-expanded")).toBe("false");
  });
});
