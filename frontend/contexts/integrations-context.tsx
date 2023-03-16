"use client";

import { Integration } from "@/models";
import { GetIntegrationResponse } from "@/types/responses";
import {
  Dispatch,
  ReactNode,
  SetStateAction,
  createContext,
  useContext,
  useState,
} from "react";

type IntegrationsType = Integration[];
type IntegrationsContextType = {
  integrations: IntegrationsType;
  setIntegrations: Dispatch<SetStateAction<IntegrationsType>>;
};

const IntegrationsContext = createContext<IntegrationsContextType | undefined>(
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
    <IntegrationsContext.Provider value={{ integrations, setIntegrations }}>
      {children}
    </IntegrationsContext.Provider>
  );
}

export const useIntegrationsContext = () => {
  const context = useContext(IntegrationsContext);
  if (context === undefined) {
    throw new Error("Expected integrations to be defined.");
  }
  return context;
};
