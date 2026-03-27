/**
 * IndexedDB helper for offline data storage.
 *
 * DB: 'bcp-itscm-offline', version 1
 * Stores: systems, procedures, contacts, incidents, cache-meta
 */

const DB_NAME = "bcp-itscm-offline";
const DB_VERSION = 1;
const STORES = [
  "systems",
  "procedures",
  "contacts",
  "incidents",
  "cache-meta",
] as const;

export type StoreName = (typeof STORES)[number];

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof indexedDB !== "undefined";
}

/**
 * Open (or create) the IndexedDB database.
 */
export function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    if (!isBrowser()) {
      reject(new Error("IndexedDB is not available in this environment"));
      return;
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      for (const store of STORES) {
        if (!db.objectStoreNames.contains(store)) {
          db.createObjectStore(store);
        }
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

/**
 * Save data to an offline store under the key "data".
 */
export async function saveToOfflineStore<T>(
  storeName: StoreName,
  data: T,
): Promise<void> {
  if (!isBrowser()) return;

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    const store = tx.objectStore(storeName);
    store.put(data, "data");
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

/**
 * Retrieve data from an offline store (key "data").
 */
export async function getFromOfflineStore<T>(
  storeName: StoreName,
): Promise<T | null> {
  if (!isBrowser()) return null;

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readonly");
    const store = tx.objectStore(storeName);
    const request = store.get("data");
    request.onsuccess = () => {
      db.close();
      resolve((request.result as T) ?? null);
    };
    request.onerror = () => {
      db.close();
      reject(request.error);
    };
  });
}

/**
 * Clear all entries from an offline store.
 */
export async function clearOfflineStore(storeName: StoreName): Promise<void> {
  if (!isBrowser()) return;

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, "readwrite");
    const store = tx.objectStore(storeName);
    store.clear();
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}

/**
 * Get the last sync time for a given store from cache-meta.
 */
export async function getLastSyncTime(
  storeName: string,
): Promise<string | null> {
  if (!isBrowser()) return null;

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("cache-meta", "readonly");
    const store = tx.objectStore("cache-meta");
    const request = store.get(`sync-${storeName}`);
    request.onsuccess = () => {
      db.close();
      resolve((request.result as string) ?? null);
    };
    request.onerror = () => {
      db.close();
      reject(request.error);
    };
  });
}

/**
 * Update the sync time for a given store to now (ISO string).
 */
export async function updateSyncTime(storeName: string): Promise<void> {
  if (!isBrowser()) return;

  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("cache-meta", "readwrite");
    const store = tx.objectStore("cache-meta");
    store.put(new Date().toISOString(), `sync-${storeName}`);
    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error);
    };
  });
}
