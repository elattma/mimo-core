"use client";

import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { clientPost } from "@/lib/client-fetchers";
import { cn, truncate } from "@/lib/util";
import { File } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function ItemUploader() {
  const [files, setFiles] = useState<File[]>([]);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      console.log(files);
      console.log(acceptedFiles);
      if (acceptedFiles.length < 1) return;
      // TODO: Add error toast
      if (files.length + acceptedFiles.length > 5) {
        console.log("You can only upload 5 files at once.");
        return;
      }
      setFiles((oldFiles) => [...oldFiles, ...acceptedFiles]);
    },
    [files]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 5,
  });

  const uploadFiles = () => {
    // TODO: Add error toast
    if (files.length < 1) {
      console.log("You must upload at least one file.");
      return;
    }
    if (process.env.NODE_ENV === "development") {
      console.log("Uploading files...");
      console.log(files);
      return;
    }
    for (const file of files) {
      clientPost("/item", {
        body: JSON.stringify({
          contentType: file.type,
          name: file.name,
        }),
      }).then(({ signedUrl }) =>
        fetch(signedUrl, { method: "PUT", body: file })
      );
    }
  };

  return (
    <>
      <div className="flex w-full flex-col space-y-theme-1/2">
        {/* Dropzone */}
        <div
          className={cn(
            "h-32 w-full cursor-pointer rounded-theme border border-dashed transition-colors",
            isDragActive
              ? "border-brand-border-hover bg-neutral-bg-hover"
              : "border-neutral-border bg-neutral-bg"
          )}
          {...getRootProps()}
        >
          <input {...getInputProps()} />
          <div className="flex h-full w-full items-center justify-center p-theme">
            <p className="select-none text-center text-sm text-gray-text">
              Drag and drop a file here, or click to open file selector.
            </p>
          </div>
        </div>
        {/* List of files */}
        {files.length > 0 && (
          <div className="flex flex-col gap-theme-1/4">
            <h2 className="font-medium text-gray-text-contrast">
              Staged Files
            </h2>
            <ul className="flex flex-col gap-theme-1/8">
              {files.map((file, index) => (
                <li
                  className="flex h-fit items-center space-x-theme-1/4"
                  key={index}
                >
                  <File className="h-4 w-4 text-gray-text-contrast" />
                  <p className="text-sm text-gray-text-contrast">
                    {truncate(file.name, 50)}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <DialogFooter className="flex w-full items-center justify-end">
        <Button onClick={uploadFiles}>Upload</Button>
      </DialogFooter>
    </>
  );
}
