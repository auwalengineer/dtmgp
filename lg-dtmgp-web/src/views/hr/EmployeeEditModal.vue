<script setup lang="ts">
import { Camera, Trash2, Undo2 } from "@lucide/vue";
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { z } from "zod";

import { DateField, FormActions, SelectField, TextareaField, TextField } from "@/components/form";
import { apiRequest, uploadFile } from "@/services/api";

import CameraCapture from "./CameraCapture.vue";
import EmployeeAvatar from "./EmployeeAvatar.vue";
import type { Options } from "./types";

/**
 * Full edit form for an existing Employee. Field set mirrors the server allowlist
 * (dtmgp.api.v1.people.EDITABLE_EMPLOYEE_FIELDS); the server remains the authority
 * on scope and validation (ADR-003). Only changed fields are sent.
 */
const props = defineProps<{ employee: string; options: Options }>();
const emit = defineEmits<{ close: []; saved: [result: { name: string; employee_name: string; changed: string[] }] }>();

const FIELDS = [
  "first_name", "middle_name", "last_name", "gender", "date_of_birth", "date_of_joining",
  "department", "designation", "status", "relieving_date", "reason_for_leaving",
  "employee_number", "dtmgp_grade_level", "dtmgp_step", "dtmgp_rank", "dtmgp_schedule_of_duty",
  "dtmgp_verification_status", "dtmgp_date_of_first_appointment", "dtmgp_date_of_present_appointment",
  "date_of_retirement", "dtmgp_local_govt_of_payment", "salary_mode", "bank_name", "bank_ac_no",
  "cell_number", "personal_email", "person_to_be_contacted", "relation", "emergency_phone_number",
  "dtmgp_lg_of_origin", "dtmgp_council_ward", "dtmgp_bvn", "dtmgp_nin", "dtmgp_qualifications",
] as const;
type Field = typeof FIELDS[number];
type FormValues = Record<Field, string>;

const scalar = z.union([z.string(), z.number(), z.null()]).optional();
const editSchema = z.object({
  values: z.record(z.string(), scalar),
  readonly: z.object({
    name: z.string(), employee_name: z.string(), company: z.string(), image: z.string().nullable().optional(),
    // True when `image` is a Desk attachment standing in for an empty Image field.
    image_from_attachment: z.boolean().optional(),
    dtmgp_retire_year_by_age: z.string().nullable().optional(), dtmgp_retire_year_by_appointment: z.string().nullable().optional(),
  }).passthrough(),
  pay_points: z.array(z.string()),
  salary_modes: z.array(z.string()),
  banks: z.array(z.string()),
});
type EditPayload = z.infer<typeof editSchema>;

const SECTIONS = ["Personal", "Service & appointment", "Pay & bank", "Contact & next of kin", "Origin"] as const;
const activeSection = ref<typeof SECTIONS[number]>("Personal");
const loading = ref(true);
const saving = ref(false);
const error = ref("");
const payload = ref<EditPayload | null>(null);
const original = ref<FormValues>(blank());
const form = ref<FormValues>(blank());
// Photo: taken with the device camera only (see CameraCapture) and applied on Save, so Cancel discards it.
const showCamera = ref(false);
const pendingPhoto = ref<File | null>(null);
const pendingPreview = ref("");
const removePhoto = ref(false);

function blank(): FormValues { return Object.fromEntries(FIELDS.map((field) => [field, ""])) as FormValues; }
const toOptions = (items: string[]) => items.map((item) => ({ value: item, label: item }));
const withNone = (items: string[], none = "Not set") => [{ value: "", label: none }, ...toOptions(items)];
// Number inputs hand back numbers through v-model, so compare as trimmed text.
const text = (value: unknown) => String(value ?? "").trim();
const changedFields = computed(() => FIELDS.filter((field) => text(form.value[field]) !== text(original.value[field])));
const isLeaving = computed(() => form.value.status === "Left");
const identityError = (value: string) => (text(value) && !/^\d{11}$/.test(text(value)) ? "Must be exactly 11 digits" : "");
const accountError = computed(() => (text(form.value.bank_ac_no) && !/^\d{10}$/.test(text(form.value.bank_ac_no)) ? "Must be a 10-digit NUBAN account number" : ""));
const paysByBank = computed(() => form.value.salary_mode === "Bank");
const bankMissing = computed(() => paysByBank.value && (!text(form.value.bank_name) || !text(form.value.bank_ac_no)));
const photoChanged = computed(() => !!pendingPhoto.value || removePhoto.value);
const changeCount = computed(() => changedFields.value.length + (photoChanged.value ? 1 : 0));
const shownImage = computed(() => (pendingPreview.value || (removePhoto.value ? null : payload.value?.readonly.image)) ?? null);
const hasClientErrors = computed(() => !!identityError(form.value.dtmgp_bvn) || !!identityError(form.value.dtmgp_nin) || (isLeaving.value && !form.value.relieving_date) || !!accountError.value || bankMissing.value);

function clearPendingPhoto() {
  if (pendingPreview.value) URL.revokeObjectURL(pendingPreview.value);
  pendingPreview.value = "";
  pendingPhoto.value = null;
}
function onPhotoCaptured(file: File) {
  clearPendingPhoto();
  pendingPhoto.value = file;
  pendingPreview.value = URL.createObjectURL(file);
  removePhoto.value = false;
  showCamera.value = false;
}
function markPhotoRemoved() { clearPendingPhoto(); removePhoto.value = true; }
function undoPhotoChange() { clearPendingPhoto(); removePhoto.value = false; }

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = editSchema.parse(await apiRequest<unknown>(`/api/method/dtmgp.api.v1.people.get_employee_for_edit?employee=${encodeURIComponent(props.employee)}`));
    payload.value = data;
    const values = blank();
    for (const field of FIELDS) values[field] = data.values[field] == null ? "" : String(data.values[field]);
    original.value = { ...values };
    form.value = values;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to load this employee";
  } finally {
    loading.value = false;
  }
}

async function save() {
  if (!changeCount.value) { emit("close"); return; }
  if (hasClientErrors.value) { error.value = "Please fix the highlighted fields."; return; }
  saving.value = true;
  error.value = "";
  const values: Record<string, string | number | null> = {};
  for (const field of changedFields.value) {
    const value = text(form.value[field]);
    values[field] = field === "dtmgp_step" ? (value ? Number(value) : null) : value;
  }
  const photoWasChanged = photoChanged.value;
  try {
    if (photoWasChanged) {
      // Private + attached to this Employee, so the file inherits its LGA-scoped read permission.
      const fileUrl = pendingPhoto.value ? (await uploadFile(pendingPhoto.value, { doctype: "Employee", docname: props.employee, isPrivate: true })).file_url : null;
      await apiRequest("/api/method/dtmgp.api.v1.people.set_employee_image", { method: "POST", body: JSON.stringify({ employee: props.employee, file_url: fileUrl }) });
      if (payload.value) payload.value.readonly.image = fileUrl;
      undoPhotoChange();
    }
    const result = changedFields.value.length
      ? await apiRequest<{ name: string; employee_name: string; changed: string[] }>("/api/method/dtmgp.api.v1.people.update_employee", {
        method: "POST", body: JSON.stringify({ employee: props.employee, values }),
      })
      : { name: props.employee, employee_name: payload.value?.readonly.employee_name || props.employee, changed: [] as string[] };
    emit("saved", { ...result, changed: photoWasChanged ? [...result.changed, "image"] : result.changed });
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Unable to save employee";
  } finally {
    saving.value = false;
  }
}

onMounted(load);
onBeforeUnmount(clearPendingPhoto);
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <form class="user-modal employee-edit-modal" aria-labelledby="employee-edit-title" @submit.prevent="save">
      <header class="employee-edit-header">
        <EmployeeAvatar v-if="payload" :name="payload.readonly.employee_name" :image="shownImage" large />
        <div>
          <h2 id="employee-edit-title">Edit employee</h2>
          <p v-if="payload">{{ payload.readonly.employee_name }} · {{ payload.readonly.name }} · {{ payload.readonly.company.replace(" Local Government Area", " LGA") }}</p>
          <div v-if="payload && !showCamera" class="employee-edit-photo-actions">
            <button type="button" class="secondary-action" @click="showCamera = true"><Camera :size="15" /> {{ shownImage ? "Retake photo" : "Take photo" }}</button>
            <button v-if="shownImage && (pendingPreview || !payload.readonly.image_from_attachment)" type="button" class="secondary-action" @click="markPhotoRemoved"><Trash2 :size="15" /> Remove</button>
            <button v-if="photoChanged" type="button" class="secondary-action" @click="undoPhotoChange"><Undo2 :size="15" /> Undo photo change</button>
            <small v-if="photoChanged">{{ removePhoto ? "Photo will be removed" : "New photo" }} — applied when you save</small>
          </div>
        </div>
      </header>

      <p v-if="loading" class="users-empty">Loading employee record...</p>
      <CameraCapture v-else-if="showCamera" @captured="onPhotoCaptured" @cancel="showCamera = false" />
      <template v-else-if="payload">
        <nav class="employee-edit-tabs" aria-label="Employee record sections">
          <button v-for="section in SECTIONS" :key="section" type="button" :class="{ active: activeSection === section }" :aria-pressed="activeSection === section" @click="activeSection = section">{{ section }}</button>
        </nav>

        <div v-show="activeSection === 'Personal'" class="form-grid">
          <TextField v-model="form.first_name" label="First name" required />
          <TextField v-model="form.middle_name" label="Middle name" />
          <TextField v-model="form.last_name" label="Last name" />
          <SelectField v-model="form.gender" label="Gender" required :options="toOptions(options.genders)" placeholder="Select gender" />
          <DateField v-model="form.date_of_birth" label="Date of birth" required />
          <TextField v-model="form.dtmgp_grade_level" label="Grade level" placeholder="GL 08" />
          <TextField v-model="form.dtmgp_step" label="Step" type="number" />
          <TextField v-model="form.dtmgp_rank" label="Rank" />
          <TextField v-model="form.dtmgp_bvn" label="BVN" :maxlength="11" :error="identityError(form.dtmgp_bvn)" />
          <TextField v-model="form.dtmgp_nin" label="NIN" :maxlength="11" :error="identityError(form.dtmgp_nin)" />
          <TextareaField v-model="form.dtmgp_qualifications" label="Qualifications" placeholder="e.g. B.Sc Accounting (2010), ANAN" />
        </div>

        <div v-show="activeSection === 'Service & appointment'" class="form-grid">
          <TextField v-model="form.employee_number" label="File no." />
          <SelectField v-model="form.status" label="Employment status" required :options="toOptions(options.statuses)" />
          <DateField v-if="isLeaving" v-model="form.relieving_date" label="Relieving date" required :error="isLeaving && !form.relieving_date ? 'Required when status is Left' : ''" />
          <TextField v-if="isLeaving" v-model="form.reason_for_leaving" label="Reason for leaving" />
          <SelectField v-model="form.department" label="Department" :options="withNone(options.departments, 'Unassigned')" />
          <SelectField v-model="form.designation" label="Designation" :options="withNone(options.designations, 'Unassigned')" />
          <TextField v-model="form.dtmgp_schedule_of_duty" label="Schedule of duty" />
          <DateField v-model="form.date_of_joining" label="Date joined" required />
          <DateField v-model="form.dtmgp_date_of_first_appointment" label="Date of 1st appointment" />
          <DateField v-model="form.dtmgp_date_of_present_appointment" label="Date of present appointment" />
          <DateField v-model="form.date_of_retirement" label="Date of retirement" hint="Leave empty to use the earlier of the two dates below" />
          <p class="employee-edit-derived full-field">
            Retires by age: <strong>{{ payload.readonly.dtmgp_retire_year_by_age || "—" }}</strong> ·
            by length of service: <strong>{{ payload.readonly.dtmgp_retire_year_by_appointment || "—" }}</strong>
            <small>(recalculated on save)</small>
          </p>
          <SelectField v-model="form.dtmgp_verification_status" label="Verification status" :options="toOptions(options.verification_statuses)" />
        </div>

        <div v-show="activeSection === 'Pay & bank'" class="form-grid">
          <SelectField v-model="form.dtmgp_local_govt_of_payment" label="Local govt. of payment (pay point)" :options="withNone(payload.pay_points)" />
          <SelectField v-model="form.salary_mode" label="Salary mode" :options="withNone(payload.salary_modes)" />
          <SelectField v-if="payload.banks.length" v-model="form.bank_name" label="Bank" :required="paysByBank" :options="withNone(payload.banks, 'Select bank')" :error="paysByBank && !form.bank_name ? 'Required when salary mode is Bank' : ''" />
          <TextField v-else v-model="form.bank_name" label="Bank" :required="paysByBank" :error="paysByBank && !form.bank_name ? 'Required when salary mode is Bank' : ''" />
          <TextField v-model="form.bank_ac_no" label="Account number (NUBAN)" :required="paysByBank" :maxlength="10" :error="accountError || (paysByBank && !text(form.bank_ac_no) ? 'Required when salary mode is Bank' : '')" />
          <p class="employee-edit-derived full-field">Bank changes are recorded in the audit trail (which fields changed, not the values).</p>
        </div>

        <div v-show="activeSection === 'Contact & next of kin'" class="form-grid">
          <TextField v-model="form.cell_number" label="Phone number" type="tel" />
          <TextField v-model="form.personal_email" label="Personal email" type="email" />
          <TextField v-model="form.person_to_be_contacted" label="Emergency contact name" />
          <TextField v-model="form.relation" label="Relationship" />
          <TextField v-model="form.emergency_phone_number" label="Emergency phone" type="tel" />
        </div>

        <div v-show="activeSection === 'Origin'" class="form-grid">
          <TextField v-model="form.dtmgp_lg_of_origin" label="LG of origin" />
          <TextField v-model="form.dtmgp_council_ward" label="Council ward" />
          <p class="employee-edit-derived full-field">The LGA can't be changed here: use a posting or transfer to move staff between LGAs.</p>
        </div>
      </template>

      <FormActions v-if="!showCamera" :saving="saving" :disabled="loading || !payload" :error="error" :save-label="changeCount ? `Save ${changeCount} change${changeCount === 1 ? '' : 's'}` : 'No changes'" @cancel="emit('close')" />
    </form>
  </div>
</template>

<style scoped>
.employee-edit-modal { max-width: 820px; }
.employee-edit-header { align-items: center; display: flex; flex-wrap: wrap; gap: 16px; }
.employee-edit-header h2 { margin: 0; }
.employee-edit-photo-actions { align-items: center; display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
.employee-edit-photo-actions button { align-items: center; display: inline-flex; gap: 6px; }
.employee-edit-photo-actions small { color: var(--muted); font-size: .72rem; }
.employee-edit-header p { color: var(--muted); font-size: .78rem; margin: 4px 0 0; }
.employee-edit-tabs { border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 4px; }
.employee-edit-tabs button { background: none; border: 0; border-bottom: 2px solid transparent; color: var(--muted); cursor: pointer; font: inherit; font-size: .8rem; padding: 8px 10px; }
.employee-edit-tabs button.active { border-bottom-color: var(--green-700); color: var(--green-900); font-weight: 600; }
.employee-edit-derived { background: var(--green-100); color: var(--ink); font-size: .76rem; margin: 0; padding: 10px 12px; }
.employee-edit-derived small { color: var(--muted); }
</style>
