import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import FileField from "./FileField.vue";

function fileList(files: File[]): FileList {
  return { ...files, length: files.length, item: (index: number) => files[index] ?? null } as unknown as FileList;
}

describe("FileField", () => {
  it("emits the selected File and shows its name", async () => {
    const wrapper = mount(FileField, { props: { label: "Evidence" } });
    const file = new File(["contents"], "evaluation-report.pdf", { type: "application/pdf" });
    const input = wrapper.find("input").element as HTMLInputElement;
    Object.defineProperty(input, "files", { value: fileList([file]) });
    await wrapper.find("input").trigger("change");

    expect(wrapper.emitted("update:modelValue")?.[0]).toEqual([file]);
    await wrapper.setProps({ modelValue: file });
    expect(wrapper.find(".field-file-name").text()).toBe("evaluation-report.pdf");
  });

  it("is only required until a file is present", () => {
    const empty = mount(FileField, { props: { label: "Evidence", required: true, modelValue: null } });
    expect(empty.find("input").attributes("required")).toBeDefined();
    const file = new File(["x"], "doc.pdf");
    const filled = mount(FileField, { props: { label: "Evidence", required: true, modelValue: file } });
    expect(filled.find("input").attributes("required")).toBeUndefined();
  });
});
