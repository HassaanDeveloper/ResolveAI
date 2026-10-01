"use client";

import { createContext, useContext, useRef, useCallback, useState, ReactNode } from "react";

type RefreshFn = () => void;

interface RefreshContextValue {
  refreshFn: RefreshFn | null;
  setRefreshFn: (fn: RefreshFn | null) => void;
}

const RefreshContext = createContext<RefreshContextValue>({
  refreshFn: null,
  setRefreshFn: () => {},
});

export function RefreshProvider({ children }: { children: ReactNode }) {
  const ref = useRef<RefreshFn | null>(null);
  const [, forceUpdate] = useState(0);
  const setRefreshFn = useCallback((fn: RefreshFn | null) => {
    ref.current = fn;
    forceUpdate(n => n + 1);
  }, []);
  const refreshFn = ref.current;

  return (
    <RefreshContext.Provider value={{ refreshFn, setRefreshFn }}>
      {children}
    </RefreshContext.Provider>
  );
}

export function useRefresh() {
  const context = useContext(RefreshContext);
  if (context === null) {
    return { refreshFn: null, setRefreshFn: () => {} };
  }
  return context;
}