import { describe, expect, it } from "vitest";

import { reportOrientation } from "./reportPrint";

describe("report print layout", () => {
  it("uses portrait for compact reports", () => {
    expect(reportOrientation({ columns: ["Status", "Count"], rows: [["Completed", 4]] })).toBe("portrait");
  });

  it("uses landscape for wide reports", () => {
    expect(reportOrientation({ columns: ["Date", "Account", "Debit", "Credit", "Voucher"], rows: [] })).toBe("landscape");
  });
});
