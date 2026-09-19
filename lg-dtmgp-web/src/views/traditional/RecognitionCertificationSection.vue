<script setup lang="ts">
import { Award, BadgeCheck, CircleX, FileText, Inbox, Undo2 } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "recognition-requests": "Recognition Requests", "recognition-approvals": "Recognition Approvals", "certificate-register": "Certificate Register", "issue-certificates": "Issue Certificates", "suspended-recognition": "Suspended Recognition", "withdrawn-recognition": "Withdrawn Recognition" };
const DEFAULT_ITEM = "recognition-requests";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'recognition-requests'">
    <PreviewCard :icon="Inbox" title="Recognition requests" body="Requests for state recognition of a traditional appointment aren't modeled yet." />
  </template>
  <template v-else-if="activeItem === 'recognition-approvals'">
    <PreviewCard :icon="BadgeCheck" title="Recognition approvals" body="An approval workflow for granting state recognition isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'certificate-register'">
    <PreviewCard :icon="FileText" title="Certificate register" body="A register of issued recognition certificates isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'issue-certificates'">
    <PreviewCard :icon="Award" title="Issue certificates" body="Certificate issuance (generation, signing, delivery) isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'suspended-recognition'">
    <PreviewCard :icon="CircleX" title="Suspended recognition" body="Tracking of suspended recognitions isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'withdrawn-recognition'">
    <PreviewCard :icon="Undo2" title="Withdrawn recognition" body="Tracking of withdrawn recognitions isn't available yet." />
  </template>
</template>
