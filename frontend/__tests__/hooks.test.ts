/**
 * Tests for the generic useApi hook.
 */
import { renderHook, act, waitFor } from "@testing-library/react";
import { useApi } from "../lib/hooks";

describe("useApi", () => {
  it("returns loading=true before fetch resolves", () => {
    // Never-resolving fetcher to freeze loading state
    const fetcher = jest.fn(() => new Promise<string>(() => {}));
    const { result } = renderHook(() => useApi(fetcher));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("sets data and loading=false after successful fetch", async () => {
    const fetcher = jest.fn().mockResolvedValue({ id: 1 });
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toEqual({ id: 1 });
    expect(result.current.error).toBeNull();
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("sets error and loading=false when fetch rejects", async () => {
    const fetcher = jest
      .fn()
      .mockRejectedValue(new Error("API unavailable"));

    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("API unavailable");
  });

  it("wraps non-Error rejections into an Error", async () => {
    const fetcher = jest.fn().mockRejectedValue("plain string error");
    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe("plain string error");
  });

  it("refetch() triggers a new fetch call", async () => {
    const fetcher = jest
      .fn()
      .mockResolvedValueOnce("first")
      .mockResolvedValueOnce("second");

    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.data).toBe("first"));

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => expect(result.current.data).toBe("second"));
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("resets error to null on successful refetch", async () => {
    const fetcher = jest
      .fn()
      .mockRejectedValueOnce(new Error("fail"))
      .mockResolvedValueOnce("ok");

    const { result } = renderHook(() => useApi(fetcher));

    await waitFor(() => expect(result.current.error).not.toBeNull());

    act(() => {
      result.current.refetch();
    });

    await waitFor(() => expect(result.current.data).toBe("ok"));
    expect(result.current.error).toBeNull();
  });
});
