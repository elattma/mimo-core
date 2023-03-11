import ItemUploader from "@/components/item-uploader";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Item } from "@/models";
import { Plus } from "lucide-react";

type UploadedItemsProps = {
  items: Item[];
};

export default function UploadedItems({ items }: UploadedItemsProps) {
  return (
    <div className="flex w-full flex-col space-y-theme-1/2">
      <div className="flex w-full items-center justify-between">
        <p className="text-sm font-semibold text-gray-text-contrast">
          Uploaded Items
        </p>
        <Dialog>
          <DialogTrigger asChild>
            <button
              className="rounded-theme p-theme-1/4 text-neutral-text outline-none transition-colors active:bg-neutral-bg-active hocus:bg-neutral-bg-hover hocus:text-neutral-text-contrast"
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
      {items.length === 0 ? (
        <div className="rounded-theme border border-dashed border-neutral-border p-theme">
          <p className="text-center text-sm text-gray-text">
            You have no uploaded items. Press the plus to add one.
          </p>
        </div>
      ) : (
        <></>
      )}
    </div>
  );
}
