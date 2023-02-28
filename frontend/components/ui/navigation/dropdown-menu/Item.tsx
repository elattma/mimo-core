"use client";

import { Item as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Item = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={[
      "flex w-full select-none items-center justify-between rounded-theme p-theme-1/4 text-sm font-medium leading-none text-gray-text outline-none transition-colors hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover focus:outline-none active:bg-neutral-bg-active",
      className,
    ].join(" ")}
    {...props}
  />
));
Item.displayName = Primitive.displayName;

export default Item;
