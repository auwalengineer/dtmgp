import { defineStore } from "pinia";

export const useSessionStore = defineStore("session", {
  state: () => ({
    user: { name: "Amina Oche", role: "State Administrator" },
    activeLga: "Statewide",
  }),
  actions: {
    setActiveLga(lga: string) {
      this.activeLga = lga;
    },
  },
});
