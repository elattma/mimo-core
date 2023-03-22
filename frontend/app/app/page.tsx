"use client";

import {
  Toast,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/ui/toast";
import { useState } from "react";

const Page = () => {
  const [open, setOpen] = useState<boolean>(true);

  return (
    <ToastProvider swipeDirection="right" swipeThreshold={100}>
      <Toast
        className="relative flex w-full items-start gap-theme rounded-theme border border-success-border bg-success-bg p-theme-1/2 shadow-md animate-in data-[state=open]:slide-in-from-right"
        variant="success"
        open={open}
        onOpenChange={setOpen}
      >
        <div className="grid gap-theme-1/4">
          <ToastTitle className="text-[13px] font-semibold leading-none text-success-text-contrast">
            Toast Title
          </ToastTitle>
          <ToastDescription className="text-[13px] leading-none text-success-text">
            Toast Description
          </ToastDescription>
        </div>
      </Toast>
      <ToastViewport />
    </ToastProvider>
  );
};

export default Page;
