"use client";

import { Item } from "@/models";
import {
  Dispatch,
  ReactNode,
  SetStateAction,
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

type SelectedItemType = Item | null;
type SelectedItemContextType = {
  selectedItem: SelectedItemType;
  setSelectedItem: Dispatch<SetStateAction<SelectedItemType>>;
};

const selectedItemContext = createContext<SelectedItemContextType | undefined>(
  undefined
);

type Props = {
  children: ReactNode;
};

export function SelectedItemProvider({ children }: Props) {
  const [selectedItem, setSelectedItem] = useState<SelectedItemType>(null);

  useEffect(() => console.log(selectedItem), [selectedItem]);

  return (
    <selectedItemContext.Provider value={{ selectedItem, setSelectedItem }}>
      {children}
    </selectedItemContext.Provider>
  );
}

export function useSelectedItemContext() {
  const context = useContext(selectedItemContext);
  if (context === undefined) {
    throw new Error(
      "useSelectedItemContext must be used within a SelectedItemProvider"
    );
  }
  return context;
}
