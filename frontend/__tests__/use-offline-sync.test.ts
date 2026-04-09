/**
 * Tests for the useOfflineSync hook.
 *
 * Key scenarios:
 * - Online: fetches from API and caches result in IndexedDB
 * - Online API error: falls back to IndexedDB cache
 * - Offline: loads from IndexedDB cache directly
 * - Online/offline toggle: responds to window events
 * - refetch(): triggers a new fetch
 */
import { IDBFactory } from "fake-indexeddb";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useOfflineSync } from "../lib/use-offline-sync";
import { saveToOfflineStore } from "../lib/indexed-db";

// Reset IndexedDB before each test for isolation
beforeEach(() => {
  globalThis.indexedDB = new IDBFactory();
});

// Simulate online status via navigator.onLine
function setNavigatorOnline(value: boolean) {
  Object.defineProperty(navigator, "onLine", {
    configurable: true,
    get: () => value,
  });
}

function fireOnlineEvent() {
  window.dispatchEvent(new Event("online"));
}

function fireOfflineEvent() {
  window.dispatchEvent(new Event("offline"));
}

describe("useOfflineSync", () => {
  beforeEach(() => {
    setNavigatorOnline(true);
  });

  it("fetches data from API when online and exposes it", async () => {
    const mockData = [{ id: 1, title: "Incident A" }];
    const fetcher = jest.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    // Initially loading
    expect(result.current.loading).toBe(true);

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(result.current.isOnline).toBe(true);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("caches API result in IndexedDB after successful fetch", async () => {
    const mockData = { status: "ok" };
    const fetcher = jest.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    // Now read from IndexedDB directly
    const { getFromOfflineStore } = await import("../lib/indexed-db");
    const cached = await getFromOfflineStore("incidents");
    expect(cached).toEqual(mockData);
  });

  it("falls back to cached data when API throws an error", async () => {
    // Pre-populate cache
    const cachedData = [{ id: 99, title: "Cached Incident" }];
    await saveToOfflineStore("incidents", cachedData);

    const fetcher = jest
      .fn()
      .mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    // Should have fallback data and an error
    expect(result.current.data).toEqual(cachedData);
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("Network error");
  });

  it("loads from IndexedDB when offline", async () => {
    const cachedData = [{ id: 5, title: "Offline Incident" }];
    await saveToOfflineStore("incidents", cachedData);
    setNavigatorOnline(false);

    const fetcher = jest.fn().mockResolvedValue([]);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual(cachedData);
    expect(result.current.isOnline).toBe(false);
    // API should NOT be called when offline
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("updates isOnline when offline event fires", async () => {
    const fetcher = jest.fn().mockResolvedValue([]);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.isOnline).toBe(true);

    act(() => {
      setNavigatorOnline(false);
      fireOfflineEvent();
    });

    await waitFor(() => expect(result.current.isOnline).toBe(false));
  });

  it("updates isOnline when online event fires", async () => {
    setNavigatorOnline(false);
    const fetcher = jest.fn().mockResolvedValue([]);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.isOnline).toBe(false);

    act(() => {
      setNavigatorOnline(true);
      fireOnlineEvent();
    });

    await waitFor(() => expect(result.current.isOnline).toBe(true));
  });

  it("refetch() triggers a new API call", async () => {
    const fetcher = jest
      .fn()
      .mockResolvedValueOnce([{ id: 1 }])
      .mockResolvedValueOnce([{ id: 2 }]);

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual([{ id: 1 }]);

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => expect(result.current.data).toEqual([{ id: 2 }]));
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("sets lastSyncTime after a successful online fetch", async () => {
    const fetcher = jest.fn().mockResolvedValue({ ok: true });

    const { result } = renderHook(() =>
      useOfflineSync("incidents", fetcher),
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.lastSyncTime).not.toBeNull();
    // Should be a valid ISO date string
    expect(new Date(result.current.lastSyncTime!).toISOString()).toBe(
      result.current.lastSyncTime,
    );
  });
});
