import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import DataTable, { type DataTableColumn } from "./DataTable.vue";

const COLUMNS: DataTableColumn[] = [
  { key: "name", label: "Project", sortable: true },
  { key: "status", label: "Status" },
];
const ROWS = [
  { name: "PROJ-1", status: "Open" },
  { name: "PROJ-2", status: "Completed" },
];

describe("DataTable", () => {
  it("renders a header and a row per record", () => {
    const wrapper = mount(DataTable, { props: { columns: COLUMNS, rows: ROWS, total: 2, page: 1, pageSize: 25 } });
    expect(wrapper.findAll("th")).toHaveLength(2);
    expect(wrapper.findAll("tbody tr")).toHaveLength(2);
    expect(wrapper.text()).toContain("PROJ-1");
    expect(wrapper.text()).toContain("Completed");
  });

  it("shows a dash for a missing value and the empty message when there are no rows", () => {
    const withGap = mount(DataTable, { props: { columns: COLUMNS, rows: [{ name: "PROJ-3", status: null }], total: 1, page: 1, pageSize: 25 } });
    expect(withGap.find("tbody tr td:last-child").text()).toBe("-");

    const empty = mount(DataTable, { props: { columns: COLUMNS, rows: [], total: 0, page: 1, pageSize: 25, emptyMessage: "No projects recorded for this LGA." } });
    expect(empty.text()).toContain("No projects recorded for this LGA.");
  });

  it("emits sort only for sortable columns", async () => {
    const wrapper = mount(DataTable, { props: { columns: COLUMNS, rows: ROWS, total: 2, page: 1, pageSize: 25 } });
    expect(wrapper.findAll(".data-table-sort")).toHaveLength(1);
    await wrapper.find(".data-table-sort").trigger("click");
    expect(wrapper.emitted("sort")?.[0]).toEqual(["name"]);
  });

  it("renders a slotted cell instead of the raw value when provided", () => {
    const wrapper = mount(DataTable, {
      props: { columns: COLUMNS, rows: ROWS, total: 2, page: 1, pageSize: 25 },
      slots: { "cell-status": "<span class=\"table-status\">Custom</span>" },
    });
    expect(wrapper.findAll(".table-status")).toHaveLength(2);
  });

  it("shows the search box only when a search value is bound, and emits updates", async () => {
    const withoutSearch = mount(DataTable, { props: { columns: COLUMNS, rows: ROWS, total: 2, page: 1, pageSize: 25 } });
    expect(withoutSearch.find(".directory-search").exists()).toBe(false);

    const withSearch = mount(DataTable, { props: { columns: COLUMNS, rows: ROWS, total: 2, page: 1, pageSize: 25, search: "" } });
    await withSearch.find(".directory-search input").setValue("Rural Road");
    expect(withSearch.emitted("update:search")?.[0]).toEqual(["Rural Road"]);
  });
});
