<script setup lang="ts">
import { TrendingUp } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { docstatusLabel } from "./types";
import type { Promotion } from "./types";

const props = defineProps<{ promotions: Promotion[]; canManage: boolean }>();
defineEmits<{ "new-review": []; "submit-promotion": [name: string] }>();

const ITEM_LABELS: Record<string, string> = { "promotion-eligibility": "Promotion Eligibility", "promotion-requests": "Promotion Requests", "promotion-reviews": "Promotion Reviews", "approved-promotions": "Approved Promotions", "promotion-history": "Promotion History" };
const DEFAULT_ITEM = "promotion-reviews";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const promotionRequests = computed(() => props.promotions.filter((p) => p.docstatus === 0));
const approvedPromotions = computed(() => props.promotions.filter((p) => p.docstatus === 1));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'promotion-eligibility'">
    <PreviewCard :icon="TrendingUp" title="Promotion eligibility" body="Eligibility evaluation (time-in-grade, qualifying exams, etc.) isn't modeled yet — promotions today are prepared manually as reviews." />
  </template>

  <template v-else-if="activeItem === 'promotion-requests'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Promotion requests</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-review')"><TrendingUp :size="15" /> New review</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th><th></th></tr></thead><tbody><tr v-for="promotion in promotionRequests" :key="promotion.name" v-record="{ doctype: 'Employee Promotion', name: promotion.name }"><td>{{ promotion.employee_name }}</td><td>{{ promotion.promotion_date }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('submit-promotion', promotion.name)">Approve</button></td></tr></tbody></table><p v-if="!promotionRequests.length" class="users-empty">No promotion requests awaiting approval.</p></div>
  </template>

  <template v-else-if="activeItem === 'promotion-reviews'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Promotion reviews</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-review')"><TrendingUp :size="15" /> New review</button></div>
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="promotion in promotions" :key="promotion.name" v-record="{ doctype: 'Employee Promotion', name: promotion.name }"><td>{{ promotion.employee_name }}</td><td>{{ promotion.promotion_date }}</td><td><span class="table-status" :class="promotion.docstatus === 1 ? 'success' : 'neutral'">{{ docstatusLabel(promotion.docstatus, 'Approved') }}</span></td><td><button v-if="canManage && promotion.docstatus === 0" class="secondary-action compact-action" @click="$emit('submit-promotion', promotion.name)">Approve</button></td></tr></tbody></table><p v-if="!promotions.length" class="users-empty">No promotion reviews recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'approved-promotions'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th></tr></thead><tbody><tr v-for="promotion in approvedPromotions" :key="promotion.name" v-record="{ doctype: 'Employee Promotion', name: promotion.name }"><td>{{ promotion.employee_name }}</td><td>{{ promotion.promotion_date }}</td></tr></tbody></table><p v-if="!approvedPromotions.length" class="users-empty">No approved promotions yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'promotion-history'">
    <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Employee</th><th>Date</th><th>Status</th></tr></thead><tbody><tr v-for="promotion in promotions" :key="promotion.name" v-record="{ doctype: 'Employee Promotion', name: promotion.name }"><td>{{ promotion.employee_name }}</td><td>{{ promotion.promotion_date }}</td><td><span class="table-status" :class="promotion.docstatus === 1 ? 'success' : 'neutral'">{{ docstatusLabel(promotion.docstatus, 'Approved') }}</span></td></tr></tbody></table><p v-if="!promotions.length" class="users-empty">No promotion history for this LGA.</p></div>
  </template>
</template>
