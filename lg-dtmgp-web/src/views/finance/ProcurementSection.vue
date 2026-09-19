<script setup lang="ts">
import { FilePlus2, PackageSearch } from "@lucide/vue";
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import ItemTabs from "../shared/ItemTabs.vue";
import PreviewCard from "../shared/PreviewCard.vue";
import { money } from "./types";
import type { ProcurementCase, ProcurementPlan } from "./types";

const props = defineProps<{ procurementPlans: ProcurementPlan[]; procurementCases: ProcurementCase[]; canManage: boolean }>();
defineEmits<{ "new-plan": []; "advance-plan": [name: string, target: string]; "advance-case": [name: string, target: string] }>();

const PLAN_NEXT_STATUS: Record<string, string> = { Draft: "Pending Approval", "Pending Approval": "Approved" };
const CASE_NEXT_STATUS: Record<string, string> = { Initiated: "Solicitation", Solicitation: "Bid Opening", "Bid Opening": "Evaluation", Evaluation: "Evaluated", Evaluated: "Pending Approval", "Pending Approval": "Approved", Approved: "Awarded", Awarded: "Completed" };
const ITEM_LABELS: Record<string, string> = { "procurement-plans": "Procurement Plans", "purchase-requests": "Purchase Requests", "requests-for-quotation": "Requests for Quotation", "supplier-quotations": "Supplier Quotations", "bid-evaluation": "Bid Evaluation", "purchase-orders": "Purchase Orders", "goods-received": "Goods Received", "procurement-approvals": "Procurement Approvals" };
const DEFAULT_ITEM = "procurement-plans";
const route = useRoute();
const activeItem = ref(String(route.params.item || "") in ITEM_LABELS ? String(route.params.item) : DEFAULT_ITEM);
watch(() => route.params.item, (item) => { activeItem.value = item && String(item) in ITEM_LABELS ? String(item) : DEFAULT_ITEM; });

const casesByStatus = (statuses: string[]) => computed(() => props.procurementCases.filter((c) => statuses.includes(c.status)));
const purchaseRequestCases = casesByStatus(["Initiated"]);
const rfqCases = casesByStatus(["Solicitation"]);
const quotationCases = casesByStatus(["Bid Opening"]);
const evaluationCases = casesByStatus(["Evaluation", "Evaluated"]);
const awardedCases = computed(() => props.procurementCases.filter((c) => c.purchase_order));
const approvalCases = casesByStatus(["Pending Approval"]);
const approvalPlans = computed(() => props.procurementPlans.filter((p) => p.status === "Pending Approval"));
</script>

<template>
  <ItemTabs :items="Object.entries(ITEM_LABELS).map(([id, label]) => ({ id, label }))" :active-id="activeItem" @select="activeItem = $event" />

  <template v-if="activeItem === 'procurement-plans'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Procurement plans</h3><button v-if="canManage" class="secondary-action" @click="$emit('new-plan')"><FilePlus2 :size="15" /> New plan</button></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Plan</th><th>Category</th><th>Method</th><th>Estimate</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="plan in procurementPlans" :key="plan.name"><td><strong>{{ plan.title }}</strong></td><td>{{ plan.procurement_category }}</td><td>{{ plan.procurement_method }}</td><td>{{ money(plan.estimated_amount) }}</td><td><span class="table-status" :class="plan.status === 'Approved' ? 'success' : 'neutral'">{{ plan.status }}</span></td><td><button v-if="canManage && PLAN_NEXT_STATUS[plan.status]" class="secondary-action compact-action" @click="$emit('advance-plan', plan.name, PLAN_NEXT_STATUS[plan.status])">Advance to {{ PLAN_NEXT_STATUS[plan.status] }}</button></td></tr></tbody></table><p v-if="!procurementPlans.length" class="users-empty">No procurement plans recorded for this LGA.</p></div>
  </template>

  <template v-else-if="activeItem === 'purchase-requests'">
    <p class="users-empty" style="text-align:left;padding:12px 20px 0">Shown as procurement cases at the Initiated stage — a separate purchase-requisition entity isn't modeled.</p>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Plan</th><th>Estimate</th><th></th></tr></thead><tbody><tr v-for="item in purchaseRequestCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.procurement_plan }}</td><td>{{ money(item.estimated_amount) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-case', item.name, CASE_NEXT_STATUS[item.status])">Advance to {{ CASE_NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!purchaseRequestCases.length" class="users-empty">No cases at the Initiated stage.</p></div>
  </template>

  <template v-else-if="activeItem === 'requests-for-quotation'">
    <p class="users-empty" style="text-align:left;padding:12px 20px 0">Shown as procurement cases at the Solicitation stage — quotations aren't captured as their own entity yet.</p>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Plan</th><th>Estimate</th><th></th></tr></thead><tbody><tr v-for="item in rfqCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.procurement_plan }}</td><td>{{ money(item.estimated_amount) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-case', item.name, CASE_NEXT_STATUS[item.status])">Advance to {{ CASE_NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!rfqCases.length" class="users-empty">No cases at the Solicitation stage.</p></div>
  </template>

  <template v-else-if="activeItem === 'supplier-quotations'">
    <p class="users-empty" style="text-align:left;padding:12px 20px 0">Shown as procurement cases at the Bid Opening stage — individual supplier quotations aren't recorded as their own entity yet.</p>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Plan</th><th>Estimate</th><th></th></tr></thead><tbody><tr v-for="item in quotationCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.procurement_plan }}</td><td>{{ money(item.estimated_amount) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-case', item.name, CASE_NEXT_STATUS[item.status])">Advance to {{ CASE_NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!quotationCases.length" class="users-empty">No cases at the Bid Opening stage.</p></div>
  </template>

  <template v-else-if="activeItem === 'bid-evaluation'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Recommended supplier</th><th>Evaluated amount</th><th>Status</th><th></th></tr></thead><tbody><tr v-for="item in evaluationCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.recommended_supplier || '-' }}</td><td>{{ item.evaluated_amount ? money(item.evaluated_amount) : '-' }}</td><td><span class="table-status neutral">{{ item.status }}</span></td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-case', item.name, CASE_NEXT_STATUS[item.status])">Advance to {{ CASE_NEXT_STATUS[item.status] }}</button></td></tr></tbody></table><p v-if="!evaluationCases.length" class="users-empty">No cases under evaluation.</p></div>
  </template>

  <template v-else-if="activeItem === 'purchase-orders'">
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Purchase order</th><th>Status</th></tr></thead><tbody><tr v-for="item in awardedCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ item.purchase_order }}</td><td><span class="table-status" :class="item.status === 'Completed' ? 'success' : 'neutral'">{{ item.status }}</span></td></tr></tbody></table><p v-if="!awardedCases.length" class="users-empty">No cases with a linked purchase order yet.</p></div>
  </template>

  <template v-else-if="activeItem === 'goods-received'">
    <PreviewCard :icon="PackageSearch" title="Goods received" body="Goods-received notes aren't modeled yet — a procurement case tracks a purchase order reference but not a separate receiving record." />
  </template>

  <template v-else-if="activeItem === 'procurement-approvals'">
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Plans awaiting approval</h3></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Plan</th><th>Estimate</th><th></th></tr></thead><tbody><tr v-for="plan in approvalPlans" :key="plan.name"><td><strong>{{ plan.title }}</strong></td><td>{{ money(plan.estimated_amount) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-plan', plan.name, 'Approved')">Approve</button></td></tr></tbody></table><p v-if="!approvalPlans.length" class="users-empty">No plans awaiting approval.</p></div>
    <div class="directory-toolbar"><h3 style="margin:0;flex:1">Cases awaiting approval</h3></div>
    <div class="staff-table-wrap"><table class="staff-table finance-table"><thead><tr><th>Case</th><th>Estimate</th><th></th></tr></thead><tbody><tr v-for="item in approvalCases" :key="item.name"><td><strong>{{ item.title }}</strong></td><td>{{ money(item.estimated_amount) }}</td><td><button v-if="canManage" class="secondary-action compact-action" @click="$emit('advance-case', item.name, 'Approved')">Approve</button></td></tr></tbody></table><p v-if="!approvalCases.length" class="users-empty">No cases awaiting approval.</p></div>
  </template>
</template>
