"use client";

import { clientPost } from "@/lib/client-fetchers";
import { cn, truncate } from "@/lib/util";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

function getTruncatedFileName(fileName: string) {
  if (fileName.length < 20) return fileName;
  const splitFileName = fileName.split(".");
  const extension = splitFileName.pop();
  const truncatedBaseName = truncate(splitFileName.join("."), 24);
  return `${truncatedBaseName}.${extension}`;
}

export default function UploadItemDropzone() {
  const [files, setFiles] = useState<File[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length < 1) return;
    setFiles(acceptedFiles);
  }, []);

  const uploadFile = useCallback(() => {
    if (files.length < 1) return;
    const file = files[0];
    clientPost("/item", {
      body: JSON.stringify({ contentType: file.type, name: file.name }),
    }).then((data) => {
      if (!data?.signedUrl) {
        console.log("issues");
        return;
      }

      if (
        process.env.NODE_ENV === "development" &&
        process.env.NEXT_PUBLIC_MOCK_OR_PROXY === "mock"
      ) {
        setFiles([]);
        return;
      }
      fetch(data.signedUrl, {
        method: "PUT",
        body: file,
        headers: { "Content-Type": file.type },
      }).then(() => setFiles([]));
    });
  }, [files]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
  });

  if (files.length > 0) {
    return (
      <div className="flex h-32 w-full grow-0 flex-col justify-between rounded-theme border border-solid bg-neutral-bg p-theme transition-colors">
        <p className="text-sm text-gray-text-contrast">
          {getTruncatedFileName(files[0].name)}
        </p>
        <button
          className="w-fit self-end rounded-theme bg-brand-solid px-theme-1/4 py-theme-1/8 text-sm font-medium text-brand-on-solid"
          onClick={uploadFile}
        >
          Upload
        </button>
      </div>
    );
  } else {
    return (
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
    );
  }
}
