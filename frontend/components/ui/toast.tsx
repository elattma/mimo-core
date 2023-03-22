import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-toast";
import { cva, VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import { ComponentPropsWithoutRef, ElementRef, forwardRef } from "react";

const ToastProvider = Primitive.Provider;

const ToastViewport = forwardRef<
  ElementRef<typeof Primitive.Viewport>,
  ComponentPropsWithoutRef<typeof Primitive.Viewport>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Viewport
    ref={forwardedRef}
    className={cn(
      "fixed bottom-theme right-theme z-[100] flex max-h-screen w-80 max-w-[100vw] flex-col items-end",
      className
    )}
    {...props}
  />
));
ToastViewport.displayName = Primitive.Viewport.displayName;

const toastVariants = cva("", {
  variants: {
    variant: {
      default: "",
      success: "",
      error: "",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

const Toast = forwardRef<
  ElementRef<typeof Primitive.Toast>,
  ComponentPropsWithoutRef<typeof Primitive.Toast> &
    VariantProps<typeof toastVariants>
>(({ className, variant, ...props }, forwardedRef) => (
  <Primitive.Toast
    ref={forwardedRef}
    className={cn(toastVariants({ variant }), className)}
    {...props}
  />
));
Toast.displayName = Primitive.Toast.displayName;

const ToastTitle = forwardRef<
  ElementRef<typeof Primitive.Title>,
  ComponentPropsWithoutRef<typeof Primitive.Title>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Title
    ref={forwardedRef}
    className={cn("", className)}
    {...props}
  />
));
ToastTitle.displayName = Primitive.Title.displayName;

const ToastDescription = forwardRef<
  ElementRef<typeof Primitive.Description>,
  ComponentPropsWithoutRef<typeof Primitive.Description>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Description
    ref={forwardedRef}
    className={cn("", className)}
    {...props}
  />
));
ToastDescription.displayName = Primitive.Description.displayName;

const ToastAction = forwardRef<
  ElementRef<typeof Primitive.Action>,
  ComponentPropsWithoutRef<typeof Primitive.Action>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Action
    ref={forwardedRef}
    className={cn("", className)}
    {...props}
  />
));
ToastAction.displayName = Primitive.Action.displayName;

const ToastClose = forwardRef<
  ElementRef<typeof Primitive.Close>,
  ComponentPropsWithoutRef<typeof Primitive.Close>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Close ref={forwardedRef} className={cn("", className)} {...props}>
    <X className="h-4 w-4" />
    <span className="sr-only">Close</span>
  </Primitive.Close>
));
ToastClose.displayName = Primitive.Close.displayName;

type ToastProps = React.ComponentPropsWithoutRef<typeof Toast>;

type ToastActionElement = React.ReactElement<typeof ToastAction>;

export {
  type ToastProps,
  type ToastActionElement,
  ToastProvider,
  ToastViewport,
  Toast,
  ToastTitle,
  ToastDescription,
  ToastAction,
  ToastClose,
};
