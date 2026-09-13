<script setup lang="ts">
import { ArrowRight, CalendarClock, CheckCircle2, CircleAlert, FileClock, FolderKanban } from "@lucide/vue";

const metrics = [
  { label: "LGAs reporting", value: "21 / 23", detail: "2 submissions outstanding", tone: "green" },
  { label: "Open resolutions", value: "146", detail: "18 due this week", tone: "gold" },
  { label: "Active projects", value: "284", detail: "₦42.8bn monitored value", tone: "blue" },
  { label: "Compliance alerts", value: "12", detail: "4 require state review", tone: "red" },
];

const actions = [
  { title: "Statutory returns", detail: "2 LGAs have not submitted August returns", icon: FileClock, type: "Overdue" },
  { title: "Council resolutions", detail: "18 actions reach their due date this week", icon: CalendarClock, type: "Due soon" },
  { title: "Project inspections", detail: "7 field reports are awaiting review", icon: FolderKanban, type: "Review" },
];
</script>

<template>
  <section class="page-heading">
    <div><p class="eyebrow">State operations</p><h1>Good morning, Amina</h1><p>Monday, 14 September 2026 · Statewide overview</p></div>
    <button class="primary-action">Create report <ArrowRight :size="17" /></button>
  </section>

  <section class="metrics-grid" aria-label="Operational summary">
    <article v-for="metric in metrics" :key="metric.label" class="metric" :class="`metric--${metric.tone}`">
      <span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.detail }}</small>
    </article>
  </section>

  <div class="overview-grid">
    <section class="panel action-panel">
      <header class="panel-header"><div><h2>Attention required</h2><p>Items needing action across the state</p></div><button class="text-action">View all <ArrowRight :size="15" /></button></header>
      <div class="action-list">
        <button v-for="action in actions" :key="action.title" class="action-row">
          <span class="action-icon"><component :is="action.icon" :size="20" /></span>
          <span class="action-copy"><strong>{{ action.title }}</strong><small>{{ action.detail }}</small></span>
          <span class="status-badge">{{ action.type }}</span><ArrowRight :size="17" />
        </button>
      </div>
    </section>

    <section class="panel reporting-panel">
      <header class="panel-header"><div><h2>Reporting status</h2><p>Current reporting cycle</p></div></header>
      <div class="progress-ring"><strong>91%</strong><span>submitted</span></div>
      <div class="reporting-legend"><p><CheckCircle2 :size="17" />21 submitted</p><p><CircleAlert :size="17" />2 outstanding</p></div>
      <button class="secondary-action">Open compliance dashboard</button>
    </section>
  </div>
</template>
