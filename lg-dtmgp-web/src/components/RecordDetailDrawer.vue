<script setup lang="ts">
import { ExternalLink, X } from "@lucide/vue";
import { computed, nextTick, ref, watch } from "vue";

import { closeRecordDetails, recordDetailState, type DetailField } from "@/services/recordDetails";

const closeButton = ref<HTMLButtonElement>();
const titleId = "record-detail-title";
const fields = computed(() => recordDetailState.record?.sections.reduce((total, section) => total + section.fields.length, 0) || 0);

watch(() => recordDetailState.open, async (open) => {
  document.body.classList.toggle("drawer-open", open);
  if (open) { await nextTick(); closeButton.value?.focus(); }
});

function isAttachment(field: DetailField) { return field.type === "Attach" || field.type === "Attach Image"; }
function displayValue(field: DetailField) {
  if (typeof field.value === "boolean") return field.value ? "Yes" : "No";
  if (field.type === "Currency" && typeof field.value === "number") return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" }).format(field.value);
  if (field.type === "Percent") return `${field.value}%`;
  return String(field.value);
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="recordDetailState.open" class="record-detail-layer" @keydown.esc="closeRecordDetails">
        <button class="record-detail-scrim" aria-label="Close record details" @click="closeRecordDetails" />
        <aside class="record-detail-drawer" role="dialog" aria-modal="true" :aria-labelledby="titleId">
          <header class="record-detail-header">
            <div>
              <p>{{ recordDetailState.record?.doctype_label || "Record details" }}</p>
              <h2 :id="titleId">{{ recordDetailState.record?.title || "Loading record" }}</h2>
            </div>
            <button ref="closeButton" class="icon-button" title="Close" aria-label="Close record details" @click="closeRecordDetails"><X :size="20" /></button>
          </header>
          <div class="record-detail-body">
            <div v-if="recordDetailState.loading" class="record-detail-state" role="status"><span class="detail-spinner" />Loading record details...</div>
            <div v-else-if="recordDetailState.error" class="record-detail-state error-state" role="alert"><strong>Could not open this record</strong><span>{{ recordDetailState.error }}</span></div>
            <template v-else-if="recordDetailState.record">
              <div class="record-detail-meta"><span class="table-status neutral">{{ recordDetailState.record.status }}</span><span>{{ recordDetailState.record.name }}</span><span>Updated {{ recordDetailState.record.modified }}</span></div>
              <section v-for="section in recordDetailState.record.sections" :key="section.label" class="record-detail-section">
                <h3>{{ section.label }}</h3>
                <dl>
                  <template v-for="field in section.fields" :key="field.label">
                    <div v-if="field.type !== 'Table'" class="record-detail-field">
                      <dt>{{ field.label }}</dt>
                      <dd><a v-if="isAttachment(field)" :href="String(field.value)" target="_blank" rel="noopener">Open attachment <ExternalLink :size="14" /></a><span v-else>{{ displayValue(field) }}</span></dd>
                    </div>
                    <div v-else class="record-detail-field detail-child-table">
                      <dt>{{ field.label }}</dt>
                      <dd v-for="(row, rowIndex) in field.value as DetailField[][]" :key="rowIndex">
                        <span v-for="cell in row" :key="cell.label"><small>{{ cell.label }}</small>{{ displayValue(cell) }}</span>
                      </dd>
                    </div>
                  </template>
                </dl>
              </section>
              <p v-if="!fields" class="record-detail-state">No displayable details are available for this record.</p>
            </template>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>
