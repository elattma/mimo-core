"use client";

import * as Primitive from "@radix-ui/react-dropdown-menu";
import { forwardRef } from "react";

const DropdownMenu = Primitive.Root;

const DropdownMenuTrigger = Primitive.Trigger;

const DropdownMenuPortal = Primitive.Portal;

const DropdownMenuContent = forwardRef<
  React.ElementRef<typeof Primitive.Content>,
  React.ComponentPropsWithoutRef<typeof Primitive.Content>
>(({ children, className, ...props }, forwardedRef) => (
  <Primitive.Content
    ref={forwardedRef}
    className={[
      "mt-theme-1/4 min-w-[8rem] rounded-theme border border-neutral-border/50 bg-neutral-base p-theme-1/8 shadow-md",
      className,
    ].join(" ")}
    collisionPadding={12}
    {...props}
  >
    {children}
  </Primitive.Content>
));
DropdownMenuContent.displayName = Primitive.Content.displayName;

const DropdownMenuItem = forwardRef<
  React.ElementRef<typeof Primitive.Item>,
  React.ComponentPropsWithoutRef<typeof Primitive.Item>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Item
    ref={forwardedRef}
    className={[
      "flex w-full select-none items-center justify-between rounded-theme p-theme-1/4 text-sm font-medium leading-none text-gray-text outline-none transition-colors hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover focus:outline-none active:bg-neutral-bg-active",
      className,
    ].join(" ")}
    {...props}
  />
));
DropdownMenuItem.displayName = Primitive.Item.displayName;

const DropdownMenuGroup = Primitive.Group;

const DropdownMenuLabel = forwardRef<
  React.ElementRef<typeof Primitive.Label>,
  React.ComponentPropsWithoutRef<typeof Primitive.Label>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Label
    ref={forwardedRef}
    className={[
      "p-theme-1/4 text-sm font-medium leading-none text-gray-text-contrast",
      className,
    ].join(" ")}
    {...props}
  />
));
DropdownMenuLabel.displayName = Primitive.Label.displayName;

const DropdownMenuSeparator = forwardRef<
  React.ElementRef<typeof Primitive.Separator>,
  React.ComponentPropsWithoutRef<typeof Primitive.Separator>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Separator
    ref={forwardedRef}
    className={[
      "-mx-theme-1/8 my-theme-1/8 h-px bg-neutral-border/50",
      className,
    ].join(" ")}
    {...props}
  />
));
DropdownMenuSeparator.displayName = Primitive.Separator.displayName;

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuPortal,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuSeparator,
};
