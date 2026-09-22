import { describe, expect, it } from "vitest";
import { formatMetric, scoreLabel } from "./types";

describe("analytics presentation", () => {
  it("marks incomplete scorecards as unranked", () => {
    expect(scoreLabel({ score: null, missing: ["revenue assessments"], stale: [] })).toContain("Not ranked");
  });
  it("formats metrics by their declared format", () => {
    expect(formatMetric({ format: "percent", value: 72.5 })).toBe("72.5%");
    expect(formatMetric({ format: "number", value: 2300 })).toBe("2,300");
  });
});
