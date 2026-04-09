import "@testing-library/jest-dom";

// Polyfill structuredClone for environments that don't have it (fake-indexeddb v6 requires it)
if (typeof globalThis.structuredClone === "undefined") {
  globalThis.structuredClone = <T>(obj: T): T => JSON.parse(JSON.stringify(obj));
}
