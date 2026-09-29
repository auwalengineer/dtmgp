<script setup lang="ts">
import { Download, Printer } from "@lucide/vue";
import { ref } from "vue";

import { apiRequest } from "@/services/api";

const props = defineProps<{ reportId: string; title: string; columns: string[]; rows: unknown[][]; company?: string }>();
const exportOpen = ref(false);
const purpose = ref("");
const exporting = ref(false);
const error = ref("");

function printReport() {
  document.body.classList.add("printing-report");
  window.print();
  window.setTimeout(() => document.body.classList.remove("printing-report"), 250);
}

async function exportReport() {
  exporting.value = true;
  error.value = "";
  try {
    const result = await apiRequest<{ filename: string; content: string }>("/api/method/dtmgp.api.v1.report_exports.export_report", {
      method: "POST",
      body: JSON.stringify({ report_id: props.reportId, title: props.title, purpose: purpose.value, columns: props.columns, rows: props.rows, company: props.company || null }),
    });
    const url = URL.createObjectURL(new Blob([result.content], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = result.filename;
    link.click();
    URL.revokeObjectURL(url);
    exportOpen.value = false;
    purpose.value = "";
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Unable to export report"; }
  finally { exporting.value = false; }
}
</script>

<template>
  <div class="report-actions" aria-label="Report actions">
    <button class="secondary-action" type="button" @click="printReport"><Printer :size="16" /> Print</button>
    <button class="secondary-action" type="button" :disabled="!rows.length" @click="exportOpen = true"><Download :size="16" /> Export CSV</button>
  </div>
  <div v-if="exportOpen" class="modal-backdrop" @click.self="exportOpen = false">
    <form class="user-modal" @submit.prevent="exportReport">
      <h2>Export {{ title }}</h2>
      <p class="modal-copy">The export is marked Internal and recorded in the audit trail.</p>
      <label>Purpose<textarea v-model="purpose" minlength="10" required placeholder="Monthly management review"></textarea></label>
      <p v-if="error" class="login-error" role="alert">{{ error }}</p>
      <footer><button type="button" class="secondary-action" @click="exportOpen = false">Cancel</button><button class="primary-action" :disabled="exporting">{{ exporting ? "Preparing..." : "Export CSV" }}</button></footer>
    </form>
  </div>
</template>
