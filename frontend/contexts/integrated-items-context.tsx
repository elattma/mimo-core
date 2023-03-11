"use client";

import { Item } from "@/models";
import { GetItemResponse } from "@/types/responses";
import { ReactNode, createContext, useContext, useState } from "react";

type IntegratedItemsType = Item[];
type IntegratedItemsContextType = {
  integratedItems: IntegratedItemsType;
  addToIntegratedItems: (item?: Item, items?: Item[]) => void;
};

const IntegratedItemsContext = createContext<
  IntegratedItemsContextType | undefined
>(undefined);

type Props = {
  children: ReactNode;
  initialData: GetItemResponse;
};

const IntegratedItemsProvider = ({ children, initialData }: Props) => {
  const [integratedItems, setIntegratedItems] = useState<IntegratedItemsType>(
    initialData.reduce((acc: Item[], integrationAndItsItems) => {
      integrationAndItsItems.items.forEach((itemData) =>
        acc.push(
          new Item(
            itemData.id,
            itemData.title,
            itemData.link,
            itemData.preview,
            integrationAndItsItems.icon,
            integrationAndItsItems.integration
          )
        )
      );
      return acc;
    }, [])
  );

  const addToIntegratedItems = (item?: Item, items?: Item[]) => {
    if (item && items)
      throw new Error("Expected only one of item and items to be set.");
    if (item) {
      setIntegratedItems((prev) => [...prev, item]);
    } else if (items) {
      setIntegratedItems((prev) => [...prev, ...items]);
    }
  };

  return (
    <IntegratedItemsContext.Provider
      value={{ integratedItems, addToIntegratedItems }}
    >
      {children}
    </IntegratedItemsContext.Provider>
  );
};

const useIntegratedItemsContext = () => {
  const context = useContext(IntegratedItemsContext);
  if (context === undefined) {
    throw new Error("Expected IntegratedItems to be defined.");
  }
  return context;
};

export { IntegratedItemsProvider, useIntegratedItemsContext };
