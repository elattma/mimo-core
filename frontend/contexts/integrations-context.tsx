"use client";

import { Integration } from "@/models";
import { GetIntegrationResponse } from "@/types/responses";
import {
  createContext,
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useState,
} from "react";

type IntegrationsType = Integration[];
type IntegrationsContextType = {
  integrations: IntegrationsType;
  setIntegrations: Dispatch<SetStateAction<IntegrationsType>>;
};

const integrationsContext = createContext<IntegrationsContextType | undefined>(
  undefined
);

type Props = {
  children: ReactNode;
  initial: GetIntegrationResponse;
};

export function IntegrationsProvider({ children, initial }: Props) {
  const [integrations, setIntegrations] = useState<IntegrationsType>(
    initial.map((integration) => Integration.fromJSON(integration))
  );

  return (
    <integrationsContext.Provider value={{ integrations, setIntegrations }}>
      {children}
    </integrationsContext.Provider>
  );
}

export const useIntegrationsContext = () => {
  const context = useContext(integrationsContext);
  if (context === undefined) {
    throw new Error("Expected integrations to be defined.");
  }
  return context;
};
