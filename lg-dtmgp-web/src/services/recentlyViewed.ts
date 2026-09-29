const KEY = "dtmgp_recently_viewed";
const MAX_ITEMS = 25;

export interface RecentlyViewedEntry { doctype: string; name: string; title: string; viewedAt: string }

/** Per-viewer convenience only (browser localStorage) -- never read back by the
 * server, never shared between devices. If storage is unavailable (private
 * browsing, cleared site data), viewing still works, it's just not remembered. */
export function recordRecentlyViewed(entry: Omit<RecentlyViewedEntry, "viewedAt">) {
  try {
    const existing = getRecentlyViewed().filter((item) => !(item.doctype === entry.doctype && item.name === entry.name));
    existing.unshift({ ...entry, viewedAt: new Date().toISOString() });
    localStorage.setItem(KEY, JSON.stringify(existing.slice(0, MAX_ITEMS)));
  } catch { /* storage unavailable -- nothing to do */ }
}

export function getRecentlyViewed(): RecentlyViewedEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function clearRecentlyViewed() {
  try { localStorage.removeItem(KEY); } catch { /* storage unavailable -- nothing to do */ }
}
