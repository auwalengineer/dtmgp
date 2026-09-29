import { reactive } from "vue";

import { apiRequest } from "./api";

export interface RecordReference { doctype: string; name: string; }
export interface DetailField { label: string; type: string; value: string | number | boolean | DetailField[][]; }
export interface DetailSection { label: string; fields: DetailField[]; }
export interface RecordDetails { doctype: string; doctype_label: string; name: string; title: string; status: string; modified: string; sections: DetailSection[]; }

export const recordDetailState = reactive<{ open: boolean; loading: boolean; error: string; record: RecordDetails | null }>({
  open: false,
  loading: false,
  error: "",
  record: null,
});

let requestNumber = 0;

export async function openRecordDetails(reference: RecordReference) {
  const currentRequest = ++requestNumber;
  recordDetailState.open = true;
  recordDetailState.loading = true;
  recordDetailState.error = "";
  recordDetailState.record = null;
  try {
    const query = new URLSearchParams({ doctype: reference.doctype, name: reference.name });
    const record = await apiRequest<RecordDetails>(`/api/method/dtmgp.api.v1.records.get_record?${query}`);
    if (currentRequest === requestNumber) recordDetailState.record = record;
  } catch (error) {
    if (currentRequest === requestNumber) recordDetailState.error = error instanceof Error ? error.message : "Unable to load this record";
  } finally {
    if (currentRequest === requestNumber) recordDetailState.loading = false;
  }
}

export function closeRecordDetails() {
  requestNumber += 1;
  recordDetailState.open = false;
}
