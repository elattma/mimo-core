"use client";

import { Item } from "@/models";
import { GetItemResponse } from "@/types/responses";
import { createContext, ReactNode, useContext, useState } from "react";

type ItemsType = Item[];
type ItemsContextType = {
  integratedItems: ItemsType;
  uploadedItems: ItemsType;
  addIntegratedItems: (items: Item[]) => void;
  addUploadedItems: (items: Item[]) => void;
};

const itemsContext = createContext<ItemsContextType | undefined>(undefined);

type Props = {
  children: ReactNode;
  initialData: GetItemResponse;
};

const ItemsProvider = ({ children, initialData }: Props) => {
  const initialItems = initialData.items.map(
    (itemData) =>
      new Item(
        itemData.id,
        itemData.title,
        itemData.link,
        itemData.icon,
        itemData.integration
      )
  );

  const [integratedItems, setIntegratedItems] = useState<ItemsType>(
    initialItems.filter((item) => item.integration !== "upload")
  );

  const [uploadedItems, setUploadedItems] = useState<ItemsType>(
    initialItems.filter((item) => item.integration === "upload")
  );

  const addIntegratedItems = (items: Item[]) => {
    setIntegratedItems((prev) => [...prev, ...items]);
  };

  const addUploadedItems = (items: Item[]) => {
    setUploadedItems((prev) => [...prev, ...items]);
  };

  return (
    <itemsContext.Provider
      value={{
        integratedItems,
        uploadedItems,
        addIntegratedItems,
        addUploadedItems,
      }}
    >
      {children}
    </itemsContext.Provider>
  );
};

const useItemsContext = () => {
  const context = useContext(itemsContext);
  if (context === undefined) {
    throw new Error("Expected items to be defined.");
  }
  return context;
};

export { ItemsProvider, useItemsContext };
