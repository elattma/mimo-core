"use client";

import ItemUploader from "@/components/item-uploader";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useItemsContext } from "@/contexts/items-context";
import { useSelectedItemContext } from "@/contexts/selected-item-context";
import { Item } from "@/models";
import { cva } from "class-variance-authority";
import { File, Plus } from "lucide-react";
import { useCallback, useState } from "react";

export default function UploadedItems() {
  return (
    <div className="flex w-full flex-col space-y-theme-1/2">
      <div className="flex w-full items-center justify-between">
        <p className="text-sm font-semibold text-gray-text-contrast">
          Uploaded Items
        </p>
        <Dialog>
          <DialogTrigger asChild>
            <button
              className="rounded-theme p-[2px] text-neutral-text outline-none transition-colors active:bg-neutral-bg-active hocus:bg-neutral-bg-hover hocus:text-neutral-text-contrast"
              aria-label="Open interface to upload an item"
            >
              <Plus className="h-4 w-4" />
            </button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle asChild>
                <h1>File Uploader</h1>
              </DialogTitle>
              <DialogDescription asChild>
                <p>Upload local files to allow Mimo to interact with them</p>
              </DialogDescription>
            </DialogHeader>
            <ItemUploader />
          </DialogContent>
        </Dialog>
      </div>
      <Items />
    </div>
  );
}

const itemVariants = cva(
  "flex select-none items-center space-x-theme-1/2 p-theme-1/2 transition-colors hover:cursor-pointer prevent-default-focus outline-none",
  {
    variants: {
      selected: {
        true: "bg-brand-bg text-brand-text-contrast hocus:bg-brand-bg-hover active:bg-brand-bg-active",
        false:
          "text-gray-text hocus:bg-neutral-bg-hover active:bg-neutral-bg-active bg-transparent",
      },
    },
  }
);

function Items() {
  const { uploadedItems } = useItemsContext();
  const { setSelectedItem } = useSelectedItemContext();
  const [selected, setSelected] = useState<number | null>(null);

  const selectOrUnselectItem = useCallback(
    (item: Item, index: number) => {
      if (selected === index) {
        setSelected(null);
        setSelectedItem(null);
      } else {
        setSelected(index);
        setSelectedItem(item);
      }
    },
    [selected]
  );

  if (uploadedItems.length === 0) {
    return (
      <div className="rounded-theme border border-dashed border-neutral-border p-theme">
        <p className="text-center text-sm text-gray-text">
          You have no uploaded items. Press the plus to add one.
        </p>
      </div>
    );
  } else {
    return (
      <ScrollArea
        className="rounded-theme border border-neutral-border bg-neutral-bg-subtle"
        innerClassName="max-h-52"
      >
        <div className="flex flex-col divide-y divide-neutral-border">
          {uploadedItems.map((item, index) => (
            <div
              className={itemVariants({ selected: selected === index })}
              role="checkbox"
              tabIndex={0}
              aria-checked={selected === index}
              aria-label={item.title}
              key={index}
              onClick={(event) => {
                selectOrUnselectItem(item, index);
                event.currentTarget.blur();
              }}
              onKeyDown={(event) => {
                if (event.key === " " || event.key === "Enter")
                  selectOrUnselectItem(item, index);
              }}
            >
              <File className="h-4 w-4 stroke-neutral-text" />
              <p className="truncate whitespace-nowrap text-sm font-medium">
                {item.title}
              </p>
            </div>
          ))}
        </div>
      </ScrollArea>
    );
  }
}
