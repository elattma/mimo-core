"use client";
import { cn } from "@/lib/util";
import { Slot } from "@radix-ui/react-slot";
import { cva, VariantProps } from "class-variance-authority";
import { ButtonHTMLAttributes, forwardRef } from "react";

const buttonVariants = cva("rounded-theme font-semibold transition-colors", {
  variants: {
    variant: {
      default:
        "bg-brand-solid text-brand-on-solid hover:bg-brand-solid-hover active:bg-brand-11",
      outline:
        "bg-transparent hover:bg-overlay-hover outline outline-1 outline-neutral-border text-gray-text active:bg-overlay-active",
      neutral:
        "bg-neutral-solid text-neutral-on-solid hover:bg-neutral-solid-hover active:bg-neutral-11",
      ghost:
        "bg-transparent hover:bg-overlay-hover text-gray-text active:bg-overlay-active",
      link: "text-gray-text bg-transparent underline active:bg-overlay-active hover:text-gray-text-contrast",
      destructive:
        "bg-danger-solid text-danger-on-solid hover:bg-danger-solid-hover active:bg-danger-11",
    },
    size: {
      default: "py-theme-1/4 px-theme-3/4 text-sm",
      sm: "py-theme-1/4 px-theme-1/2 text-xs",
      lg: "py-theme-1/4 px-theme text-base",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});

type ButtonProps = {
  asChild?: boolean;
} & ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, forwardedRef) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={forwardedRef}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  }
);

export { Button };
