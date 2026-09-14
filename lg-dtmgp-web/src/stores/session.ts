import { defineStore } from "pinia";
import { apiRequest, login as loginRequest, setCsrfToken } from "@/services/api";

interface UserContext { user: { email: string; full_name: string; roles: string[] }; allowed_lgas: string[]; active_lga: string | null; can_change_lga: boolean; can_manage_users: boolean; csrf_token: string }

export const useSessionStore = defineStore("session", {
  state: () => ({ initialized: false, authenticated: false, user: { email: "", name: "", role: "" }, allowedLgas: [] as string[], activeLga: "", canChangeLga: false, canManageUsers: false }),
  getters: { userInitials: (state) => state.user.name.split(" ").filter(Boolean).map((part) => part[0]).slice(0, 2).join("") },
  actions: {
    async restore() { try { this.applyContext(await apiRequest<UserContext>("/api/method/dtmgp.api.v1.context.get_current_user_context")); } catch { this.clear(); } finally { this.initialized = true; } },
    async login(username: string, password: string) { await loginRequest(username, password); await this.restore(); if (!this.authenticated) throw new Error("Unable to start your session"); },
    async logout() { await apiRequest("/api/method/logout"); this.clear(); this.initialized = true; },
    setActiveLga(lga: string) { if (this.canChangeLga && this.allowedLgas.includes(lga)) this.activeLga = lga; },
    applyContext(context: UserContext) { this.authenticated = true; this.user = { email: context.user.email, name: context.user.full_name, role: context.user.roles.find((role) => !["All", "Desk User"].includes(role)) || "Staff" }; this.allowedLgas = context.allowed_lgas; this.activeLga = context.active_lga || ""; this.canChangeLga = context.can_change_lga; this.canManageUsers = context.can_manage_users; setCsrfToken(context.csrf_token); },
    clear() { this.authenticated = false; this.user = { email: "", name: "", role: "" }; this.allowedLgas = []; this.activeLga = ""; this.canChangeLga = false; this.canManageUsers = false; setCsrfToken(""); },
  },
});
