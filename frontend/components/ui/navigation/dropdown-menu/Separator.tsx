"use client";

import { Separator as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Separator = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={[
      "-mx-theme-1/8 my-theme-1/8 h-px bg-neutral-border/50",
      className,
    ].join(" ")}
    {...props}
  />
));
Separator.displayName = Primitive.displayName;

export default Separator;
