import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { useSessionStore } from "./session";
describe("session LGA scope", () => {
  beforeEach(() => setActivePinia(createPinia()));
  it("pins an LGA officer", () => { const s = useSessionStore(); s.applyContext({ user: { email: "hr@example.com", full_name: "HR Officer", roles: ["HR Officer"] }, allowed_lgas: ["Makurdi Local Government Area"], active_lga: "Makurdi Local Government Area", can_change_lga: false, can_manage_users: false, can_view_hr: true, can_manage_hr: true, can_view_finance: false, can_manage_finance: false, navigation: { modules: [], global: [] }, csrf_token: "test" }); s.setActiveLga("Gboko Local Government Area"); expect(s.activeLga).toBe("Makurdi Local Government Area"); });
  it("allows a state administrator", () => { const s = useSessionStore(); s.applyContext({ user: { email: "admin@example.com", full_name: "State Admin", roles: ["State Administrator"] }, allowed_lgas: ["Makurdi Local Government Area", "Gboko Local Government Area"], active_lga: "Makurdi Local Government Area", can_change_lga: true, can_manage_users: true, can_view_hr: true, can_manage_hr: true, can_view_finance: true, can_manage_finance: true, navigation: { modules: [], global: [] }, csrf_token: "test" }); s.setActiveLga("Gboko Local Government Area"); expect(s.activeLga).toBe("Gboko Local Government Area"); });
});
