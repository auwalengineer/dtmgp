<script setup lang="ts">
import { ChevronDown, ChevronUp, Search } from "@lucide/vue";

import TablePager from "./TablePager.vue";

export interface DataTableColumn { key: string; label: string; sortable?: boolean; format?: (row: Record<string, unknown>) => string }

const props = defineProps<{
  columns: DataTableColumn[];
  rows: Record<string, unknown>[];
  total: number;
  page: number;
  pageSize: number;
  rowKey?: string;
  loading?: boolean;
  emptyMessage?: string;
  sortKey?: string;
  sortDir?: "asc" | "desc";
  search?: string;
  searchPlaceholder?: string;
}>();
const emit = defineEmits<{ "change-page": [delta: number]; "update:search": [value: string]; sort: [key: string] }>();

function cellText(column: DataTableColumn, row: Record<string, unknown>) {
  if (column.format) return column.format(row);
  const value = row[column.key];
  return value === null || value === undefined || value === "" ? "-" : String(value);
}
function rowKeyFor(row: Record<string, unknown>, index: number) {
  return props.rowKey ? String(row[props.rowKey]) : index;
}
</script>

<template>
  <form v-if="search !== undefined" class="directory-toolbar" @submit.prevent>
    <label class="directory-search">
      <Search :size="17" />
      <input :value="search" type="search" :placeholder="searchPlaceholder || 'Search'" @input="emit('update:search', ($event.target as HTMLInputElement).value)" />
    </label>
  </form>

  <div class="staff-table-wrap">
    <table class="staff-table finance-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key">
            <button v-if="column.sortable" type="button" class="data-table-sort" @click="emit('sort', column.key)">
              {{ column.label }}
              <ChevronUp v-if="sortKey === column.key && sortDir === 'asc'" :size="12" />
              <ChevronDown v-else-if="sortKey === column.key && sortDir === 'desc'" :size="12" />
            </button>
            <template v-else>{{ column.label }}</template>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, index) in rows" :key="rowKeyFor(row, index)">
          <td v-for="column in columns" :key="column.key">
            <slot :name="`cell-${column.key}`" :row="row">{{ cellText(column, row) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="loading" class="users-empty">Loading...</p>
    <p v-else-if="!rows.length" class="users-empty">{{ emptyMessage || "No records found." }}</p>
  </div>

  <TablePager v-if="!loading && total > 0" :page="page" :page-size="pageSize" :total="total" :item-count="rows.length" @change-page="(delta) => emit('change-page', delta)" />
</template>
