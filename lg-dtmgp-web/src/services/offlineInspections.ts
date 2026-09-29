export interface QueuedInspection {
  id?: number;
  values: Record<string, string | number>;
  photo: Blob | null;
  fileName: string | null;
  queuedAt: string;
}

const DB_NAME = "dtmgp-field-capture";
const STORE = "inspections";

function database(): Promise<IDBDatabase> {
  if (typeof indexedDB === "undefined") return Promise.reject(new Error("Offline inspection storage is unavailable in this browser"));
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function queueInspection(values: Record<string, string | number>, photo: File | null) {
  const db = await database();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction(STORE, "readwrite");
    transaction.objectStore(STORE).add({ values, photo, fileName: photo?.name || null, queuedAt: new Date().toISOString() });
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

export async function drainInspectionQueue(sync: (entry: QueuedInspection) => Promise<void>) {
  if (typeof indexedDB === "undefined") return 0;
  const db = await database();
  const entries = await new Promise<QueuedInspection[]>((resolve, reject) => {
    const request = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  for (const entry of entries) {
    try {
      await sync(entry);
      await new Promise<void>((resolve, reject) => {
        const transaction = db.transaction(STORE, "readwrite");
        transaction.objectStore(STORE).delete(entry.id!);
        transaction.oncomplete = () => resolve();
        transaction.onerror = () => reject(transaction.error);
      });
    } catch {
      break;
    }
  }
  db.close();
  return entries.length;
}
