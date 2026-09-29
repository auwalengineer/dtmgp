import { mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it, vi } from "vitest";

import { useTableQueryState } from "./useTableQueryState";

function harness() {
  return defineComponent({
    setup() {
      return useTableQueryState();
    },
    render() { return h("div"); },
  });
}

async function withRouter() {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:pathMatch(.*)*", component: { render: () => h("div") } }] });
  await router.push("/list");
  const wrapper = mount(harness(), { global: { plugins: [router] } });
  return { router, wrapper };
}

describe("useTableQueryState", () => {
  it("defaults to page 1 with no query params", async () => {
    const { wrapper } = await withRouter();
    expect(wrapper.vm.page).toBe(1);
    expect(wrapper.vm.search).toBe("");
  });

  it("writes page changes to the URL and omits page=1", async () => {
    const { router, wrapper } = await withRouter();
    wrapper.vm.changePage(1);
    await vi.waitFor(() => expect(router.currentRoute.value.query.page).toBe("2"));

    wrapper.vm.changePage(-1);
    await vi.waitFor(() => expect(router.currentRoute.value.query.page).toBeUndefined());
  });

  it("resets the page when the search term changes", async () => {
    const { router, wrapper } = await withRouter();
    wrapper.vm.changePage(1);
    await vi.waitFor(() => expect(router.currentRoute.value.query.page).toBe("2"));
    wrapper.vm.search = "Rural Road";
    await vi.waitFor(() => expect(router.currentRoute.value.query.search).toBe("Rural Road"));
    expect(router.currentRoute.value.query.page).toBeUndefined();
  });

  it("toggles sort direction on repeated clicks of the same column", async () => {
    const { router, wrapper } = await withRouter();
    wrapper.vm.toggleSort("name");
    await vi.waitFor(() => expect(router.currentRoute.value.query.sort).toBe("name"));
    expect(router.currentRoute.value.query.dir).toBeUndefined();

    wrapper.vm.toggleSort("name");
    await vi.waitFor(() => expect(router.currentRoute.value.query.dir).toBe("desc"));
  });

  it("namespaces query keys with a prefix so two tables don't collide", async () => {
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: "/:pathMatch(.*)*", component: { render: () => h("div") } }] });
    await router.push("/list");
    const Component = defineComponent({ setup() { return useTableQueryState("contracts"); }, render() { return h("div"); } });
    const wrapper = mount(Component, { global: { plugins: [router] } });
    wrapper.vm.changePage(1);
    await vi.waitFor(() => expect(router.currentRoute.value.query.contracts_page).toBe("2"));
    expect(router.currentRoute.value.query.page).toBeUndefined();
  });
});
