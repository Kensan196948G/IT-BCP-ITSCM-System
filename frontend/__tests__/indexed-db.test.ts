/**
 * Tests for IndexedDB helper functions.
 * Uses fake-indexeddb to simulate IDB in Node.js/jsdom.
 */
import { IDBFactory } from "fake-indexeddb";
import {
  openDB,
  saveToOfflineStore,
  getFromOfflineStore,
  clearOfflineStore,
  getLastSyncTime,
  updateSyncTime,
} from "../lib/indexed-db";

// Reset IndexedDB before each test for isolation
beforeEach(() => {
  globalThis.indexedDB = new IDBFactory();
});

describe("indexed-db helpers", () => {
  describe("openDB", () => {
    it("opens the database and returns an IDBDatabase", async () => {
      const db = await openDB();
      expect(db).toBeDefined();
      expect(db.name).toBe("bcp-itscm-offline");
      db.close();
    });

    it("creates required object stores on first open", async () => {
      const db = await openDB();
      const stores = Array.from(db.objectStoreNames);
      expect(stores).toContain("systems");
      expect(stores).toContain("procedures");
      expect(stores).toContain("contacts");
      expect(stores).toContain("incidents");
      expect(stores).toContain("cache-meta");
      db.close();
    });
  });

  describe("saveToOfflineStore / getFromOfflineStore", () => {
    it("saves and retrieves data correctly", async () => {
      const payload = { id: 1, name: "test-incident" };
      await saveToOfflineStore("incidents", payload);
      const result = await getFromOfflineStore("incidents");
      expect(result).toEqual(payload);
    });

    it("returns null when store is empty", async () => {
      const result = await getFromOfflineStore<string>("contacts");
      expect(result).toBeNull();
    });

    it("overwrites existing data on subsequent saves", async () => {
      await saveToOfflineStore("systems", { version: 1 });
      await saveToOfflineStore("systems", { version: 2 });
      const result = await getFromOfflineStore<{ version: number }>("systems");
      expect(result?.version).toBe(2);
    });
  });

  describe("clearOfflineStore", () => {
    it("removes all data from a store", async () => {
      await saveToOfflineStore("procedures", { step: "evacuate" });
      await clearOfflineStore("procedures");
      const result = await getFromOfflineStore("procedures");
      expect(result).toBeNull();
    });
  });

  describe("getLastSyncTime / updateSyncTime", () => {
    it("returns null before any sync", async () => {
      const time = await getLastSyncTime("incidents");
      expect(time).toBeNull();
    });

    it("returns an ISO string after updateSyncTime", async () => {
      const before = new Date();
      await updateSyncTime("incidents");
      const after = new Date();

      const syncTime = await getLastSyncTime("incidents");
      expect(syncTime).not.toBeNull();

      const parsed = new Date(syncTime!);
      expect(parsed.getTime()).toBeGreaterThanOrEqual(before.getTime() - 100);
      expect(parsed.getTime()).toBeLessThanOrEqual(after.getTime() + 100);
    });

    it("updates sync time on repeated calls", async () => {
      await updateSyncTime("systems");
      const first = await getLastSyncTime("systems");

      await new Promise((r) => setTimeout(r, 10));

      await updateSyncTime("systems");
      const second = await getLastSyncTime("systems");

      expect(new Date(second!).getTime()).toBeGreaterThanOrEqual(
        new Date(first!).getTime(),
      );
    });
  });
});
