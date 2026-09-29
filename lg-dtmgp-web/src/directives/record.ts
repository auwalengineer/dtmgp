import type { Directive } from "vue";

import { openRecordDetails, type RecordReference } from "@/services/recordDetails";

type RecordElement = HTMLElement & { __recordOpen?: (event: Event) => void; __recordKey?: (event: KeyboardEvent) => void };
const INTERACTIVE = "a, button, input, select, textarea, label, [role='button'], [contenteditable='true']";

function bind(element: RecordElement, reference: RecordReference) {
  element.__recordOpen = (event) => {
    if ((event.target as HTMLElement).closest(INTERACTIVE)) return;
    void openRecordDetails(reference);
  };
  element.__recordKey = (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    if ((event.target as HTMLElement).closest(INTERACTIVE)) return;
    event.preventDefault();
    void openRecordDetails(reference);
  };
  element.classList.add("record-row");
  element.tabIndex = 0;
  element.setAttribute("aria-label", `View ${reference.doctype} ${reference.name}`);
  element.addEventListener("click", element.__recordOpen);
  element.addEventListener("keydown", element.__recordKey);
}

function unbind(element: RecordElement) {
  if (element.__recordOpen) element.removeEventListener("click", element.__recordOpen);
  if (element.__recordKey) element.removeEventListener("keydown", element.__recordKey);
}

export const recordDirective: Directive<RecordElement, RecordReference> = {
  mounted(element, binding) {
    bind(element, binding.value);
  },
  updated(element, binding) {
    unbind(element);
    bind(element, binding.value);
  },
  unmounted: unbind,
};
