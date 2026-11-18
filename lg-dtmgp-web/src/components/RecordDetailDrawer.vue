<script setup lang="ts">
import { ExternalLink, Maximize2, X } from "@lucide/vue";
import { computed, nextTick, ref, watch } from "vue";

import { closeRecordDetails, recordDetailState, type DetailField } from "@/services/recordDetails";

import ImageLightbox from "./ImageLightbox.vue";
import RecordTimeline from "./workflow/RecordTimeline.vue";

const closeButton = ref<HTMLButtonElement>();
const titleId = "record-detail-title";
const fields = computed(() => recordDetailState.record?.sections.reduce((total, section) => total + section.fields.length, 0) || 0);

const expanded = ref(false);
const imageFailed = ref(false);
watch(() => recordDetailState.record?.image, () => { imageFailed.value = false; expanded.value = false; });

watch(() => recordDetailState.open, async (open) => {
  if (!open) expanded.value = false;
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
              <button v-if="recordDetailState.record.image && !imageFailed" type="button" class="record-detail-photo" :title="`View full-size photo of ${recordDetailState.record.title}`" @click="expanded = true">
                <img :src="recordDetailState.record.image" :alt="`Photo of ${recordDetailState.record.title}`" @error="imageFailed = true" />
                <span class="record-detail-photo-hint"><Maximize2 :size="14" /> Expand</span>
              </button>
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
              <section class="record-detail-section">
                <h3>History</h3>
                <RecordTimeline :doctype="recordDetailState.record.doctype" :name="recordDetailState.record.name" />
              </section>
            </template>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
  <ImageLightbox v-if="expanded && recordDetailState.record?.image" :src="recordDetailState.record.image" :alt="`Photo of ${recordDetailState.record.title}`" :caption="recordDetailState.record.title" @close="expanded = false" />
</template>

<style scoped>
.record-detail-photo { background: #0f1a15; border: 0; border-radius: 8px; cursor: zoom-in; display: block; height: 200px; margin: 0 0 14px; overflow: hidden; padding: 0; position: relative; width: 100%; }
.record-detail-photo img { height: 100%; object-fit: contain; width: 100%; }
.record-detail-photo-hint { align-items: center; background: rgb(0 0 0 / 55%); border-radius: 4px; bottom: 8px; color: #fff; display: inline-flex; font-size: .72rem; gap: 4px; padding: 3px 7px; position: absolute; right: 8px; }
.record-detail-photo:focus-visible { outline: 3px solid var(--gold); outline-offset: 2px; }
</style>
