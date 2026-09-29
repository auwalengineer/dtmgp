import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

/**
 * Keeps a table's page/search/sort state in the URL query string, so reloading or
 * sharing a link preserves what the user was looking at. Any table -- DataTable.vue
 * or a hand-rolled one -- can opt in by calling this and binding its returned refs;
 * it deliberately does not own rendering. Pass a `prefix` when more than one table
 * appears on the same route (e.g. under different tabs) so their query keys don't
 * collide.
 */
export function useTableQueryState(prefix = "") {
  const route = useRoute();
  const router = useRouter();
  const key = (name: string) => (prefix ? `${prefix}_${name}` : name);

  function queryString(name: string): string {
    const value = route.query[key(name)];
    return typeof value === "string" ? value : "";
  }

  function updateQuery(patch: Record<string, string | undefined>) {
    const query: Record<string, string | string[]> = {};
    for (const [k, v] of Object.entries(route.query)) {
      if (typeof v === "string") query[k] = v;
    }
    for (const [k, v] of Object.entries(patch)) {
      if (v === undefined || v === "") delete query[k];
      else query[k] = v;
    }
    router.replace({ query });
  }

  const page = computed({
    get: () => Number(queryString("page")) || 1,
    set: (value: number) => updateQuery({ [key("page")]: value > 1 ? String(value) : undefined }),
  });
  const search = computed({
    get: () => queryString("search"),
    set: (value: string) => updateQuery({ [key("search")]: value || undefined, [key("page")]: undefined }),
  });
  const sortKey = computed({
    get: () => queryString("sort"),
    set: (value: string) => updateQuery({ [key("sort")]: value || undefined }),
  });
  const sortDir = computed<"asc" | "desc">({
    get: () => (queryString("dir") === "desc" ? "desc" : "asc"),
    set: (value: "asc" | "desc") => updateQuery({ [key("dir")]: value === "desc" ? "desc" : undefined }),
  });

  function changePage(delta: number) {
    page.value = Math.max(1, page.value + delta);
  }

  function toggleSort(newKey: string) {
    const nextDir = sortKey.value === newKey && sortDir.value === "asc" ? "desc" : "asc";
    updateQuery({ [key("sort")]: newKey, [key("dir")]: nextDir === "desc" ? "desc" : undefined, [key("page")]: undefined });
  }

  return { page, search, sortKey, sortDir, changePage, toggleSort };
}
