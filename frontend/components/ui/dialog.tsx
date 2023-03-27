"use client";

import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import { forwardRef, HTMLAttributes } from "react";

const Dialog = Primitive.Root;

const DialogTrigger = Primitive.Trigger;

const DialogPortal = ({
  className,
  children,
  ...props
}: Primitive.DialogPortalProps) => (
  <Primitive.Portal className={cn(className)} {...props}>
    <div className="fixed inset-0 z-50 flex items-start justify-center sm:items-center">
      {children}
    </div>
  </Primitive.Portal>
);
DialogPortal.displayName = Primitive.Portal.displayName;

const DialogOverlay = forwardRef<
  React.ElementRef<typeof Primitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof Primitive.Overlay>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Overlay
    ref={forwardedRef}
    className={cn(
      "fixed inset-0 z-50 bg-black/50 backdrop-blur-sm transition-all duration-100 data-[state=open]:animate-in data-[state=open]:fade-in",
      className
    )}
    {...props}
  />
));
DialogOverlay.displayName = Primitive.Overlay.displayName;

const DialogContent = forwardRef<
  React.ElementRef<typeof Primitive.Content>,
  React.ComponentPropsWithoutRef<typeof Primitive.Content>
>(({ children, className, ...props }, forwardedRef) => (
  <DialogPortal>
    <DialogOverlay />
    <Primitive.Content
      ref={forwardedRef}
      className={cn(
        "fixed z-50 grid w-full gap-theme rounded-theme bg-neutral-base p-theme data-[state=open]:animate-in data-[state=open]:fade-in data-[state=open]:slide-in-from-bottom-theme-2 sm:max-w-lg",
        className
      )}
      {...props}
    >
      {children}
      <DialogClose
        className={cn(
          "text-neural-text absolute top-theme right-theme rounded-theme p-theme-1/4 transition-colors active:bg-neutral-bg-active hocus:bg-neutral-bg-hover hocus:text-neutral-text-contrast",
          className
        )}
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </DialogClose>
    </Primitive.Content>
  </DialogPortal>
));
DialogContent.displayName = Primitive.Content.displayName;

const DialogClose = forwardRef<
  React.ElementRef<typeof Primitive.Close>,
  React.ComponentPropsWithoutRef<typeof Primitive.Close>
>(({ ...props }, forwardedRef) => (
  <Primitive.Close ref={forwardedRef} {...props} />
));
DialogClose.displayName = Primitive.Close.displayName;

const DialogTitle = forwardRef<
  React.ElementRef<typeof Primitive.Title>,
  React.ComponentPropsWithoutRef<typeof Primitive.Title>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Title
    ref={forwardedRef}
    className={cn("text-lg font-semibold text-gray-text-contrast", className)}
    {...props}
  />
));
DialogTitle.displayName = Primitive.Title.displayName;

const DialogDescription = forwardRef<
  React.ElementRef<typeof Primitive.Description>,
  React.ComponentPropsWithoutRef<typeof Primitive.Description>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Description
    ref={forwardedRef}
    className={cn("text-sm text-gray-text", className)}
    {...props}
  />
));
DialogDescription.displayName = Primitive.Description.displayName;

const DialogHeader = ({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("w-full", className)} {...props} />
);
DialogHeader.displayName = "DialogHeader";

const DialogFooter = ({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("", className)} {...props} />
);
DialogFooter.displayName = "DialogFooter";

export {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogDescription,
  DialogHeader,
  DialogFooter,
  DialogClose,
};
