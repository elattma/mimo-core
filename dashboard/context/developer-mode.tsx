"use client";

import { createContext, useContext, useState } from "react";

type DeveloperModeContext = {
  developerMode: boolean;
  setDeveloperMode: React.Dispatch<React.SetStateAction<boolean>>;
};

const developerModeContext = createContext<DeveloperModeContext | undefined>(
  undefined
);

type DeveloperModeProviderProps = {
  children: React.ReactNode;
};

export function DeveloperModeProvider({
  children,
}: DeveloperModeProviderProps) {
  const [developerMode, setDeveloperMode] = useState<boolean>(true);

  return (
    <developerModeContext.Provider value={{ developerMode, setDeveloperMode }}>
      {children}
    </developerModeContext.Provider>
  );
}

export function useDeveloperModeContext() {
  const context = useContext(developerModeContext);
  if (context === undefined) {
    throw new Error(
      "useDeveloperMode used in a component that is not wrapped by a DeveloperModeProvider"
    );
  }
  return context;
}
