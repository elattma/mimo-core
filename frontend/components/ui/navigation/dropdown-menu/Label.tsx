"use client";

import { Label as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Label = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={["", className].join(" ")}
    {...props}
  />
));
Label.displayName = Primitive.displayName;

export default Label;
