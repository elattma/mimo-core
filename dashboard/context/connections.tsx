"use client";

import { createContext, useContext, useState } from "react";
import type { Connection } from "@/types";

type ConnectionsContext = {
  connections: Connection[];
  addConnection: (connection: Connection) => void;
  removeConnection: (connectionToRemove: Connection) => void;
};

const connectionsContext = createContext<ConnectionsContext | undefined>(
  undefined
);

type ConnectionsProviderProps = {
  children: React.ReactNode;
  initialConnections: Connection[];
};

export function ConnectionsProvider({
  children,
  initialConnections,
}: ConnectionsProviderProps) {
  const [connections, setConnections] =
    useState<Connection[]>(initialConnections);

  const addConnection = (connection: Connection) => {
    setConnections([...connections, connection]);
  };

  const removeConnection = (connectionToRemove: Connection) => {
    setConnections(
      connections.filter(
        (connection) => connection.id !== connectionToRemove.id
      )
    );
  };

  return (
    <connectionsContext.Provider
      value={{ connections, addConnection, removeConnection }}
    >
      {children}
    </connectionsContext.Provider>
  );
}

export function useConnectionsContext() {
  const context = useContext(connectionsContext);
  if (context === undefined) {
    throw new Error(
      "useConnectionsContext used in a component that is not wrapped by an IntegrationsProvider"
    );
  }
  return context;
}
