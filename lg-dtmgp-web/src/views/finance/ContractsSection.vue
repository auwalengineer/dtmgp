<script setup lang="ts">
import { Award, CircleCheck, FileStack, Flag, GitCommitHorizontal, Users } from "@lucide/vue";
import { ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";

const ITEM_LABELS: Record<string, string> = { "contract-register": "Contract Register", "contractor-profiles": "Contractor Profiles", "contract-milestones": "Contract Milestones", "certificates-payments": "Certificates & Payments", "contract-variations": "Contract Variations", "contract-completion": "Contract Completion" };
const DEFAULT_ITEM = "contract-register";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'contract-register'">
    <PreviewCard :icon="FileStack" title="Contract register" body="A post-award contract register isn't modeled yet — Procurement tracks a case through to award, but no distinct contract entity exists yet for milestones, certificates or variations." />
  </template>
  <template v-else-if="activeItem === 'contractor-profiles'">
    <PreviewCard :icon="Users" title="Contractor profiles" body="Contractor profile records (performance history, blacklist status) aren't available yet." />
  </template>
  <template v-else-if="activeItem === 'contract-milestones'">
    <PreviewCard :icon="Flag" title="Contract milestones" body="Contract milestone tracking isn't available yet." />
  </template>
  <template v-else-if="activeItem === 'certificates-payments'">
    <PreviewCard :icon="Award" title="Certificates & payments" body="Interim certificates and milestone payments aren't available yet." />
  </template>
  <template v-else-if="activeItem === 'contract-variations'">
    <PreviewCard :icon="GitCommitHorizontal" title="Contract variations" body="Contract variation orders aren't available yet." />
  </template>
  <template v-else-if="activeItem === 'contract-completion'">
    <PreviewCard :icon="CircleCheck" title="Contract completion" body="Contract completion sign-off isn't available yet — Procurement Cases reach a Completed status, but that isn't the same as a certified contract close-out." />
  </template>
</template>
