import { defineStore } from "pinia";
import { apiRequest, login as loginRequest, setCsrfToken } from "@/services/api";

export interface NavigationItem { id: string; label: string; to: string | null; children?: NavigationItem[] }
export interface NavigationModule extends NavigationItem { icon: string; children: NavigationItem[] }
interface UserContext { user: { email: string; full_name: string; roles: string[] }; allowed_lgas: string[]; active_lga: string | null; can_change_lga: boolean; can_manage_users: boolean; can_view_hr: boolean; can_manage_hr: boolean; can_view_finance: boolean; can_manage_finance: boolean; navigation: { modules: NavigationModule[]; global: NavigationItem[] }; csrf_token: string }

export const useSessionStore = defineStore("session", {
  state: () => ({ initialized: false, authenticated: false, user: { email: "", name: "", role: "" }, allowedLgas: [] as string[], activeLga: "", canChangeLga: false, canManageUsers: false, canViewHr: false, canManageHr: false, canViewFinance: false, canManageFinance: false, navigation: [] as NavigationModule[], globalMenu: [] as NavigationItem[] }),
  getters: { userInitials: (state) => state.user.name.split(" ").filter(Boolean).map((part) => part[0]).slice(0, 2).join("") },
  actions: {
    async restore() { try { this.applyContext(await apiRequest<UserContext>("/api/method/dtmgp.api.v1.context.get_current_user_context")); } catch { this.clear(); } finally { this.initialized = true; } },
    async login(username: string, password: string) { await loginRequest(username, password); await this.restore(); if (!this.authenticated) throw new Error("Unable to start your session"); },
    async logout() { await apiRequest("/api/method/logout"); this.clear(); this.initialized = true; },
    setActiveLga(lga: string) { if (this.canChangeLga && this.allowedLgas.includes(lga)) this.activeLga = lga; },
    applyContext(context: UserContext) { this.authenticated = true; this.user = { email: context.user.email, name: context.user.full_name, role: context.user.roles.find((role) => !["All", "Desk User"].includes(role)) || "Staff" }; this.allowedLgas = context.allowed_lgas; this.activeLga = context.active_lga || ""; this.canChangeLga = context.can_change_lga; this.canManageUsers = context.can_manage_users; this.canViewHr = context.can_view_hr; this.canManageHr = context.can_manage_hr; this.canViewFinance = context.can_view_finance; this.canManageFinance = context.can_manage_finance; this.navigation = context.navigation.modules; this.globalMenu = context.navigation.global; setCsrfToken(context.csrf_token); },
    clear() { this.authenticated = false; this.user = { email: "", name: "", role: "" }; this.allowedLgas = []; this.activeLga = ""; this.canChangeLga = false; this.canManageUsers = false; this.canViewHr = false; this.canManageHr = false; this.canViewFinance = false; this.canManageFinance = false; this.navigation = []; this.globalMenu = []; setCsrfToken(""); },
  },
});
