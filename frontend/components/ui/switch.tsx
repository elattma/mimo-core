"use client";

import * as Primitive from "@radix-ui/react-switch";
import { forwardRef } from "react";

const Switch = forwardRef<
  React.ElementRef<typeof Primitive.Root>,
  React.ComponentPropsWithoutRef<typeof Primitive.Root>
>(({ children, className, ...props }, forwardedRef) => (
  <Primitive.Root
    ref={forwardedRef}
    className={[
      "flex h-[18px] w-9 items-center justify-center rounded-full bg-neutralA-8 transition-colors data-[state=checked]:bg-brand-9",
      className,
    ].join(" ")}
    {...props}
  >
    {children}
  </Primitive.Root>
));
Switch.displayName = Primitive.Root.displayName;

const SwitchThumb = forwardRef<
  React.ElementRef<typeof Primitive.Thumb>,
  React.ComponentPropsWithoutRef<typeof Primitive.Thumb>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Thumb
    ref={forwardedRef}
    className={[
      "absolute h-3.5 w-3.5 -translate-x-[9px] rounded-full bg-neutralA-11 transition-all data-[state=checked]:translate-x-[9px] data-[state=checked]:bg-brand-3",
      className,
    ].join(" ")}
    {...props}
  />
));
SwitchThumb.displayName = Primitive.Thumb.displayName;

export { Switch, SwitchThumb };
