"use client";

import { createContext, useContext } from "react";
import type { Integration } from "@/types";

type IntegrationsContext = {
  integrations: Integration[];
};

const integrationsContext = createContext<IntegrationsContext | undefined>(
  undefined
);

type IntegrationsProviderProps = {
  children: React.ReactNode;
  integrations: Integration[];
};

export function IntegrationsProvider({
  children,
  integrations,
}: IntegrationsProviderProps) {
  return (
    <integrationsContext.Provider value={{ integrations }}>
      {children}
    </integrationsContext.Provider>
  );
}

export function useIntegrationsContext() {
  const context = useContext(integrationsContext);
  if (context === undefined) {
    throw new Error(
      "useIntegrationsContext used in a component that is not wrapped by an IntegrationsProvider"
    );
  }
  return context;
}
