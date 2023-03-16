"use client";

import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-scroll-area";
import { ComponentPropsWithoutRef, ElementRef, forwardRef } from "react";

type ScrollAreaProps = {
  innerClassName?: string;
};

const ScrollArea = forwardRef<
  ElementRef<typeof Primitive.Root>,
  ComponentPropsWithoutRef<typeof Primitive.Root> & ScrollAreaProps
>(
  (
    { children, className, onScroll, innerClassName = "", ...props },
    forwardedRef
  ) => (
    <Primitive.Root
      ref={forwardedRef}
      className={cn("overflow-hidden", className)}
      {...props}
    >
      <Primitive.Viewport
        className={cn("h-full w-full", innerClassName)}
        onScroll={onScroll}
      >
        {children}
      </Primitive.Viewport>
      <Primitive.Scrollbar
        className="duration-[160ms] flex w-theme-1/4 touch-none select-none transition-colors ease-out"
        orientation="vertical"
      >
        <Primitive.Thumb className="relative flex-1 rounded-full bg-neutralA-8" />
      </Primitive.Scrollbar>
      <Primitive.Scrollbar
        className="duration-[160ms] h-theme-1/4 touch-none select-none flex-col transition-colors ease-out"
        orientation="horizontal"
      >
        <Primitive.Thumb className="relative flex-1 rounded-full bg-neutralA-8" />
      </Primitive.Scrollbar>
      <Primitive.Corner className="h-theme-1/4 w-theme-1/4" />
    </Primitive.Root>
  )
);

export { ScrollArea };
