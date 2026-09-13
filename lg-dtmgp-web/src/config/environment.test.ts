import { describe, expect, it } from "vitest";

import { loadEnvironment } from "./environment";

describe("environment", () => {
  it("loads a valid build environment", async () => {
    const environment = await loadEnvironment();
    expect(["development", "staging", "production"]).toContain(environment.environment);
  });
});
