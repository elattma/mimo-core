"use client";

import { Item as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Item = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={["", className].join(" ")}
    {...props}
  />
));
Item.displayName = Primitive.displayName;

export default Item;
