<script setup lang="ts">
import { Search, X } from "@lucide/vue";
import { computed, onBeforeUnmount, ref, watch } from "vue";

import { apiRequest } from "@/services/api";
import { useSessionStore } from "@/stores/session";

import EmployeeAvatar from "./EmployeeAvatar.vue";
import type { Employee } from "./types";

/**
 * Searchable staff picker (ARIA combobox). Searches the whole LGA on the server
 * (name, staff ID, designation), not just the directory page that's loaded.
 */
const props = defineProps<{ label?: string }>();
const selected = defineModel<string>({ required: true });

const session = useSessionStore();
const RESULT_LIMIT = 20;
const DEBOUNCE_MS = 250;
const id = `employee-picker-${Math.random().toString(36).slice(2, 8)}`;

const query = ref("");
const open = ref(false);
const loading = ref(false);
const error = ref("");
const results = ref<Employee[]>([]);
const total = ref(0);
const activeIndex = ref(-1);
const chosen = ref<Employee | null>(null);
let timer: ReturnType<typeof setTimeout> | undefined;
let requestNumber = 0;

const chosenLabel = computed(() => (chosen.value ? `${chosen.value.employee_name} — ${chosen.value.name}` : ""));

async function search() {
  const current = ++requestNumber;
  loading.value = true;
  error.value = "";
  try {
    const params = new URLSearchParams({ company: session.activeLga, page: "1", page_size: String(RESULT_LIMIT) });
    if (query.value.trim()) params.set("search", query.value.trim());
    const result = await apiRequest<{ items: Employee[]; total: number }>(`/api/method/dtmgp.api.v1.people.list_employees?${params}`);
    if (current !== requestNumber) return;
    results.value = result.items;
    total.value = result.total;
    activeIndex.value = result.items.length ? 0 : -1;
  } catch (reason) {
    if (current === requestNumber) { results.value = []; error.value = reason instanceof Error ? reason.message : "Search failed"; }
  } finally {
    if (current === requestNumber) loading.value = false;
  }
}

function scheduleSearch() {
  clearTimeout(timer);
  timer = setTimeout(search, DEBOUNCE_MS);
}

function openList() {
  if (open.value) return;
  open.value = true;
  search();
}

function onInput() {
  open.value = true;
  scheduleSearch();
}

function choose(employee: Employee) {
  chosen.value = employee;
  selected.value = employee.name;
  query.value = "";
  open.value = false;
}

function clear() {
  chosen.value = null;
  selected.value = "";
  query.value = "";
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    if (!open.value) return openList();
    if (results.value.length) activeIndex.value = (activeIndex.value + 1) % results.value.length;
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    if (results.value.length) activeIndex.value = (activeIndex.value - 1 + results.value.length) % results.value.length;
  } else if (event.key === "Enter") {
    if (open.value && results.value[activeIndex.value]) { event.preventDefault(); choose(results.value[activeIndex.value]); }
  } else if (event.key === "Escape") {
    if (open.value) { event.preventDefault(); open.value = false; }
  }
}

// Close after focus leaves the whole picker (not when moving into the list).
function onFocusOut(event: FocusEvent) {
  const next = event.relatedTarget as Node | null;
  if (!next || !(event.currentTarget as HTMLElement).contains(next)) open.value = false;
}

// A new LGA invalidates the selection and results.
watch(() => session.activeLga, () => { clear(); results.value = []; });
// Selection cleared from outside.
watch(selected, (value) => { if (!value) chosen.value = null; });
onBeforeUnmount(() => clearTimeout(timer));

const placeholder = computed(() => chosenLabel.value || "Search name, staff ID or designation");
</script>

<template>
  <div class="employee-picker" @focusout="onFocusOut">
    <label :for="`${id}-input`">{{ props.label || "Staff member" }}</label>
    <div class="employee-picker-field" :class="{ chosen: !!chosen }">
      <Search :size="16" aria-hidden="true" />
      <input
        :id="`${id}-input`"
        v-model="query"
        type="text"
        role="combobox"
        autocomplete="off"
        aria-autocomplete="list"
        :aria-expanded="open"
        :aria-controls="`${id}-list`"
        :aria-activedescendant="open && activeIndex >= 0 ? `${id}-option-${activeIndex}` : undefined"
        :placeholder="placeholder"
        @focus="openList"
        @click="openList"
        @input="onInput"
        @keydown="onKeydown"
      />
      <button v-if="chosen" type="button" class="icon-button" aria-label="Clear selected staff member" title="Clear" @click="clear"><X :size="16" /></button>
    </div>
    <div v-show="open" class="employee-picker-popup">
      <ul :id="`${id}-list`" role="listbox" :aria-label="props.label || 'Staff member'">
        <li
          v-for="(employee, index) in results"
          :id="`${id}-option-${index}`"
          :key="employee.name"
          role="option"
          :aria-selected="index === activeIndex"
          :class="{ active: index === activeIndex, current: employee.name === selected }"
          @mousedown.prevent="choose(employee)"
          @mousemove="activeIndex = index"
        >
          <EmployeeAvatar :name="employee.employee_name" :image="employee.image" />
          <span><strong>{{ employee.employee_name }}</strong><small>{{ employee.name }} · {{ employee.designation || "No designation" }}{{ employee.status !== "Active" ? ` · ${employee.status}` : "" }}</small></span>
        </li>
      </ul>
      <p v-if="loading" class="employee-picker-status" role="status">Searching…</p>
      <p v-else-if="error" class="employee-picker-status error" role="alert">{{ error }}</p>
      <p v-else-if="!results.length" class="employee-picker-status" role="status">No staff match “{{ query.trim() }}”.</p>
      <p v-else-if="total > results.length" class="employee-picker-status">Showing {{ results.length }} of {{ total.toLocaleString() }} — keep typing to narrow the list.</p>
    </div>
  </div>
</template>

<style scoped>
.employee-picker { display: flex; flex: 1; flex-direction: column; gap: 4px; max-width: 440px; position: relative; }
.employee-picker > label { color: var(--muted); font-size: .75rem; }
.employee-picker-field { align-items: center; background: #fff; border: 1px solid var(--line); color: var(--muted); display: flex; gap: 8px; height: 40px; padding: 0 6px 0 12px; }
.employee-picker-field:focus-within { border-color: var(--green-700); box-shadow: inset 0 0 0 1px var(--green-700); }
.employee-picker-field input { border: 0; flex: 1; font: inherit; min-width: 0; outline: 0; }
.employee-picker-field.chosen input::placeholder { color: var(--text, #1d2a23); opacity: 1; }
.employee-picker-popup { background: #fff; border: 1px solid var(--line); box-shadow: 0 10px 28px rgb(15 26 21 / 14%); left: 0; max-height: 340px; overflow-y: auto; position: absolute; right: 0; top: 100%; z-index: 20; }
.employee-picker-popup ul { list-style: none; margin: 0; padding: 4px 0; }
.employee-picker-popup li { align-items: center; cursor: pointer; display: flex; gap: 10px; padding: 7px 12px; }
.employee-picker-popup li.active { background: var(--green-100); }
.employee-picker-popup li.active small { color: var(--green-900); }
.employee-picker-popup li.current strong { color: var(--green-700); }
.employee-picker-popup li span { display: flex; flex-direction: column; min-width: 0; }
.employee-picker-popup strong { font-size: .8rem; }
.employee-picker-popup small { color: var(--muted); font-size: .7rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.employee-picker-status { color: var(--muted); font-size: .72rem; margin: 0; padding: 8px 12px; }
.employee-picker-status.error { color: #a4262c; }
@media (max-width: 760px) { .employee-picker { max-width: none; } }
</style>
