import { beforeEach, describe, expect, it } from "vitest";

import { clearRecentlyViewed, getRecentlyViewed, recordRecentlyViewed } from "./recentlyViewed";

describe("recentlyViewed", () => {
  beforeEach(() => clearRecentlyViewed());

  it("records the most recently viewed record first", () => {
    recordRecentlyViewed({ doctype: "DTMGP Contract", name: "CON-MKD-2026-00001", title: "Road Contract" });
    recordRecentlyViewed({ doctype: "DTMGP Revenue Head", name: "REV-MKD-2026-00001", title: "Market Stall Fee" });
    const items = getRecentlyViewed();
    expect(items).toHaveLength(2);
    expect(items[0].name).toBe("REV-MKD-2026-00001");
  });

  it("moves a re-viewed record back to the front instead of duplicating it", () => {
    recordRecentlyViewed({ doctype: "DTMGP Contract", name: "CON-1", title: "First" });
    recordRecentlyViewed({ doctype: "DTMGP Revenue Head", name: "REV-1", title: "Second" });
    recordRecentlyViewed({ doctype: "DTMGP Contract", name: "CON-1", title: "First" });
    const items = getRecentlyViewed();
    expect(items).toHaveLength(2);
    expect(items[0].name).toBe("CON-1");
  });

  it("caps the list at 25 entries", () => {
    for (let index = 0; index < 30; index += 1) {
      recordRecentlyViewed({ doctype: "DTMGP Contract", name: `CON-${index}`, title: `Contract ${index}` });
    }
    expect(getRecentlyViewed()).toHaveLength(25);
  });

  it("clears the list", () => {
    recordRecentlyViewed({ doctype: "DTMGP Contract", name: "CON-1", title: "First" });
    clearRecentlyViewed();
    expect(getRecentlyViewed()).toEqual([]);
  });
});
