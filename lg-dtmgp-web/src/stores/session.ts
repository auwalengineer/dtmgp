import { defineStore } from "pinia";

const STATE_ROLES = new Set(["State Administrator", "State Executive Viewer", "State Auditor"]);

export const useSessionStore = defineStore("session", {
  state: () => ({
    user: { name: "Amina Oche", role: "HR Officer" },
    allowedLgas: ["Makurdi Local Government Area"],
    activeLga: "Makurdi Local Government Area",
  }),
  getters: {
    canChangeLga: (state) => STATE_ROLES.has(state.user.role) && state.allowedLgas.length > 1,
    userInitials: (state) => state.user.name.split(" ").map((part) => part[0]).slice(0, 2).join(""),
  },
  actions: {
    setActiveLga(lga: string) {
      if (!this.canChangeLga || !this.allowedLgas.includes(lga)) return;
      this.activeLga = lga;
    },
  },
});
