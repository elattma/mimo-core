"use client";

import { Content as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Content = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ children, className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={["", className].join(" ")}
    {...props}
  >
    {children}
  </Primitive>
));
Content.displayName = Primitive.displayName;

export default Content;
