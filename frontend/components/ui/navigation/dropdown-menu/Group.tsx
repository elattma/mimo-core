"use client";

import { Group as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Group = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={["", className].join(" ")}
    {...props}
  />
));
Group.displayName = Primitive.displayName;

export default Group;
