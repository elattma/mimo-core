"use client";

import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-dropdown-menu";
import { Check } from "lucide-react";
import { ComponentPropsWithoutRef, ElementRef, forwardRef } from "react";

const DropdownMenu = Primitive.Root;

const DropdownMenuTrigger = Primitive.Trigger;

const DropdownMenuPortal = Primitive.Portal;

const DropdownMenuContent = forwardRef<
  ElementRef<typeof Primitive.Content>,
  ComponentPropsWithoutRef<typeof Primitive.Content>
>(({ children, className, ...props }, forwardedRef) => (
  <DropdownMenuPortal>
    <Primitive.Content
      ref={forwardedRef}
      className={cn(
        "prevent-default-focus z-50 mt-theme-1/4 min-w-[8rem] rounded-theme border border-neutral-border/50 bg-neutral-base p-theme-1/8 shadow-md animate-in data-[side=right]:slide-in-from-left-2 data-[side=left]:slide-in-from-right-2 data-[side=bottom]:slide-in-from-top-2 data-[side=top]:slide-in-from-bottom-2",
        className
      )}
      collisionPadding={12}
      {...props}
    >
      {children}
    </Primitive.Content>
  </DropdownMenuPortal>
));
DropdownMenuContent.displayName = Primitive.Content.displayName;

const DropdownMenuItem = forwardRef<
  ElementRef<typeof Primitive.Item>,
  ComponentPropsWithoutRef<typeof Primitive.Item>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Item
    ref={forwardedRef}
    className={cn(
      "prevent-default-focus flex w-full select-none items-center justify-between rounded-theme p-theme-1/4 text-sm font-medium leading-none text-gray-text outline-none transition-colors hover:cursor-default hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover focus:outline-none active:bg-neutral-bg-active",
      className
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = Primitive.Item.displayName;

const DropdownMenuGroup = Primitive.Group;

const DropdownMenuLabel = forwardRef<
  ElementRef<typeof Primitive.Label>,
  ComponentPropsWithoutRef<typeof Primitive.Label>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Label
    ref={forwardedRef}
    className={cn(
      "p-theme-1/4 text-sm font-medium leading-none text-gray-text-contrast",
      className
    )}
    {...props}
  />
));
DropdownMenuLabel.displayName = Primitive.Label.displayName;

const DropdownMenuSeparator = forwardRef<
  ElementRef<typeof Primitive.Separator>,
  ComponentPropsWithoutRef<typeof Primitive.Separator>
>(({ className, ...props }, forwardedRef) => (
  <Primitive.Separator
    ref={forwardedRef}
    className={cn(
      "-mx-theme-1/8 my-theme-1/8 h-px bg-neutral-border/50",
      className
    )}
    {...props}
  />
));
DropdownMenuSeparator.displayName = Primitive.Separator.displayName;

const DropdownMenuCheckboxItem = forwardRef<
  ElementRef<typeof Primitive.CheckboxItem>,
  ComponentPropsWithoutRef<typeof Primitive.CheckboxItem>
>(({ children, className, checked, onSelect, ...props }, forwardedRef) => (
  <Primitive.CheckboxItem
    ref={forwardedRef}
    className={cn(
      "prevent-default-focus flex w-full select-none items-center justify-between rounded-theme p-theme-1/4 pl-theme text-sm font-medium leading-none text-gray-text outline-none transition-colors hover:cursor-default hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover focus:outline-none active:bg-neutral-bg-active",
      className
    )}
    checked={checked}
    onSelect={onSelect || ((event) => event.preventDefault())}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <Primitive.ItemIndicator>
        <Check className="h-4 w-4 text-gray-text" />
      </Primitive.ItemIndicator>
    </span>
    {children}
  </Primitive.CheckboxItem>
));
DropdownMenuCheckboxItem.displayName = Primitive.CheckboxItem.displayName;

export {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
};
