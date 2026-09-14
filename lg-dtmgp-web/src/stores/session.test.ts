import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";

import { useSessionStore } from "./session";

describe("session LGA scope", () => {
  beforeEach(() => setActivePinia(createPinia()));

  it("keeps an LGA officer pinned to the assigned LGA", () => {
    const session = useSessionStore();
    session.setActiveLga("Gboko Local Government Area");
    expect(session.canChangeLga).toBe(false);
    expect(session.activeLga).toBe("Makurdi Local Government Area");
  });

  it("allows a state administrator to select an allowed LGA", () => {
    const session = useSessionStore();
    session.user.role = "State Administrator";
    session.allowedLgas = ["Makurdi Local Government Area", "Gboko Local Government Area"];
    session.setActiveLga("Gboko Local Government Area");
    expect(session.activeLga).toBe("Gboko Local Government Area");
  });
});
