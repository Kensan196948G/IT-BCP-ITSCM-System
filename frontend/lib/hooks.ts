"use client";

import { useState, useEffect, useCallback } from "react";
import { systems, exercises, incidents, dashboard, procedures, contacts } from "./api";
import type {
  ITSystemBCP,
  BCPExercise,
  ActiveIncident,
  DashboardReadiness,
  RTOOverview,
  RecoveryProcedure,
  EmergencyContact,
  VendorContact,
} from "./types";

interface UseApiResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useApi<T>(fetcher: () => Promise<T>): UseApiResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [trigger, setTrigger] = useState(0);

  const refetch = useCallback(() => {
    setTrigger((prev) => prev + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)));
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);

  return { data, loading, error, refetch };
}

export function useSystems(): UseApiResult<ITSystemBCP[]> {
  return useApi(() => systems.list());
}

export function useExercises(): UseApiResult<BCPExercise[]> {
  return useApi(() => exercises.list());
}

export function useIncidents(): UseApiResult<ActiveIncident[]> {
  return useApi(() => incidents.list());
}

export function useDashboard(): UseApiResult<DashboardReadiness> {
  return useApi(() => dashboard.readiness());
}

export function useRTOOverview(): UseApiResult<RTOOverview> {
  return useApi(() => dashboard.rtoOverview());
}

export function useProcedures(): UseApiResult<RecoveryProcedure[]> {
  return useApi(() => procedures.list());
}

export function useEmergencyContacts(): UseApiResult<EmergencyContact[]> {
  return useApi(() => contacts.emergency.list());
}

export function useVendorContacts(): UseApiResult<VendorContact[]> {
  return useApi(() => contacts.vendors.list());
}
