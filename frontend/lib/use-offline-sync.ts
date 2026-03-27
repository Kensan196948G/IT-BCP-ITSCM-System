"use client";

import { useState, useEffect, useCallback } from "react";
import type { StoreName } from "./indexed-db";
import {
  saveToOfflineStore,
  getFromOfflineStore,
  getLastSyncTime,
  updateSyncTime,
} from "./indexed-db";

interface UseOfflineSyncResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  isOnline: boolean;
  lastSyncTime: string | null;
  isSyncing: boolean;
  refetch: () => void;
}

/**
 * Hook that fetches data from the API when online and caches it in IndexedDB.
 * Falls back to cached data when offline.
 */
export function useOfflineSync<T>(
  storeName: StoreName,
  apiFetcher: () => Promise<T>,
): UseOfflineSyncResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );
  const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => {
    setTrigger((prev) => prev + 1);
  }, []);

  // Listen for online/offline events
  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
    }
    function handleOffline() {
      setIsOnline(false);
    }

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Fetch data: online -> API + cache, offline -> IndexedDB
  useEffect(() => {
    let cancelled = false;

    async function fetchData() {
      setLoading(true);
      setError(null);

      // Load cached sync time
      try {
        const syncTime = await getLastSyncTime(storeName);
        if (!cancelled) setLastSyncTime(syncTime);
      } catch {
        // ignore
      }

      if (isOnline) {
        // Online: fetch from API
        setIsSyncing(true);
        try {
          const result = await apiFetcher();
          if (cancelled) return;
          setData(result);

          // Save to IndexedDB cache
          await saveToOfflineStore(storeName, result);
          await updateSyncTime(storeName);
          const newSyncTime = await getLastSyncTime(storeName);
          if (!cancelled) {
            setLastSyncTime(newSyncTime);
          }
        } catch (err: unknown) {
          if (cancelled) return;
          // On API error, fall back to cached data
          try {
            const cached = await getFromOfflineStore<T>(storeName);
            if (!cancelled) {
              if (cached) {
                setData(cached);
              }
              setError(
                err instanceof Error ? err : new Error(String(err)),
              );
            }
          } catch {
            if (!cancelled) {
              setError(
                err instanceof Error ? err : new Error(String(err)),
              );
            }
          }
        } finally {
          if (!cancelled) {
            setIsSyncing(false);
            setLoading(false);
          }
        }
      } else {
        // Offline: load from IndexedDB
        try {
          const cached = await getFromOfflineStore<T>(storeName);
          if (!cancelled) {
            setData(cached);
          }
        } catch (err: unknown) {
          if (!cancelled) {
            setError(
              err instanceof Error ? err : new Error(String(err)),
            );
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      }
    }

    fetchData();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeName, isOnline, trigger]);

  return { data, loading, error, isOnline, lastSyncTime, isSyncing, refetch };
}
