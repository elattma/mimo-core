"use client";

import { Content as Primitive } from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const Content = forwardRef<
  React.ElementRef<typeof Primitive>,
  React.ComponentPropsWithoutRef<typeof Primitive>
>(({ children, className, ...props }, forwardedRef) => (
  <Primitive
    ref={forwardedRef}
    className={[
      "mt-theme-1/4 min-w-[8rem] rounded-theme border border-neutral-border/50 bg-neutral-base p-theme-1/8 shadow-md",
      className,
    ].join(" ")}
    collisionPadding={12}
    {...props}
  >
    {children}
  </Primitive>
));
Content.displayName = Primitive.displayName;

export default Content;
