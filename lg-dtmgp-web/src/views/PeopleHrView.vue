<script setup lang="ts">
import { BadgeCheck, CalendarDays, ChevronRight, CircleAlert, Download, Filter, Search, UserPlus, UsersRound } from "@lucide/vue";
import { computed, ref } from "vue";

import { useSessionStore } from "@/stores/session";

const session = useSessionStore();
const activeTab = ref("Staff directory");
const search = ref("");
const staff = [
  { id: "HR-00184", name: "Terna Akume", role: "Principal Administrative Officer", department: "Administration", grade: "GL 12", status: "Active", verification: "Verified", initials: "TA" },
  { id: "HR-00231", name: "Msendoo Iorfa", role: "Senior Executive Officer", department: "Finance & Treasury", grade: "GL 10", status: "Active", verification: "Verified", initials: "MI" },
  { id: "HR-00307", name: "Oche Francis", role: "Works Superintendent", department: "Works & Housing", grade: "GL 09", status: "On Leave", verification: "Review due", initials: "OF" },
  { id: "HR-00392", name: "Ngutor Aondo", role: "Community Development Officer", department: "Social Development", grade: "GL 08", status: "Active", verification: "Pending", initials: "NA" },
  { id: "HR-00416", name: "Dooshima Ude", role: "Procurement Officer", department: "Procurement", grade: "GL 10", status: "Active", verification: "Verified", initials: "DU" },
];
const filteredStaff = computed(() => {
  const term = search.value.toLowerCase().trim();
  return term ? staff.filter((person) => [person.name, person.role, person.department, person.id].some((value) => value.toLowerCase().includes(term))) : staff;
});
</script>

<template>
  <section class="hr-heading">
    <div><p class="eyebrow">{{ session.activeLga.replace(" Local Government Area", " LGA") }}</p><h1>People & HR</h1><p>Workforce records, verification and staff administration</p></div>
    <button class="primary-action"><UserPlus :size="17" /> Add staff</button>
  </section>
  <section class="hr-metrics" aria-label="Workforce summary">
    <article><span class="hr-metric-icon green"><UsersRound :size="19" /></span><div><small>Total staff</small><strong>1,284</strong><p><b>+18</b> this quarter</p></div></article>
    <article><span class="hr-metric-icon blue"><BadgeCheck :size="19" /></span><div><small>Verified records</small><strong>1,146</strong><p>89.3% complete</p></div></article>
    <article><span class="hr-metric-icon gold"><CalendarDays :size="19" /></span><div><small>On leave</small><strong>42</strong><p>17 returning this week</p></div></article>
    <article><span class="hr-metric-icon red"><CircleAlert :size="19" /></span><div><small>Needs attention</small><strong>96</strong><p>Records to review</p></div></article>
  </section>
  <section class="hr-workspace">
    <nav class="hr-tabs" aria-label="People and HR views"><button v-for="tab in ['Staff directory', 'Verification', 'Leave & attendance', 'Establishment']" :key="tab" :class="{ active: activeTab === tab }" @click="activeTab = tab">{{ tab }}</button></nav>
    <template v-if="activeTab === 'Staff directory'">
      <header class="directory-toolbar"><label class="directory-search"><Search :size="17" /><input v-model="search" type="search" placeholder="Search staff, role or department" /></label><button class="secondary-action"><Filter :size="16" /> Filters</button><button class="icon-button export-button" title="Export staff directory"><Download :size="18" /></button></header>
      <div class="staff-table-wrap"><table class="staff-table"><thead><tr><th>Staff member</th><th>Department</th><th>Grade</th><th>Employment</th><th>Verification</th><th></th></tr></thead><tbody>
        <tr v-for="person in filteredStaff" :key="person.id"><td><div class="staff-person"><span>{{ person.initials }}</span><div><strong>{{ person.name }}</strong><small>{{ person.id }} · {{ person.role }}</small></div></div></td><td>{{ person.department }}</td><td>{{ person.grade }}</td><td><span class="table-status" :class="person.status === 'Active' ? 'success' : 'neutral'">{{ person.status }}</span></td><td><span class="verification-status" :class="person.verification === 'Verified' ? 'verified' : 'pending'">{{ person.verification }}</span></td><td><button class="icon-button" title="Open staff record"><ChevronRight :size="18" /></button></td></tr>
      </tbody></table><footer class="table-footer"><span>Showing {{ filteredStaff.length }} of 1,284 staff</span><div><button disabled>Previous</button><button class="current">1</button><button>2</button><button>3</button><button>Next</button></div></footer></div>
    </template>
    <div v-else class="hr-tab-preview"><BadgeCheck :size="34" /><h2>{{ activeTab }}</h2><p>Operational records for {{ session.activeLga.replace(" Local Government Area", " LGA") }}</p><button class="secondary-action">Open {{ activeTab.toLowerCase() }} <ChevronRight :size="16" /></button></div>
  </section>
</template>
