"use client";

import { cva } from "class-variance-authority";
import Link from "next/link";
import { useSelectedLayoutSegment } from "next/navigation";
import type { NavItem } from "@/types";

const mainNavItemVariants = cva(
  "font-medium transition-colors hover:text-foreground/80 text-sm",
  {
    variants: {
      active: {
        true: "text-foreground",
        false: "text-foreground/60",
      },
    },
  }
);

type MainNavProps = {
  items: NavItem[];
};

export function MainNav({ items }: MainNavProps) {
  const segment = useSelectedLayoutSegment();

  return (
    <nav className="flex items-end gap-6 self-end">
      {items.map((item, index) => (
        <Link
          className={mainNavItemVariants({
            active: item.href.startsWith(`/dashboard/${segment ?? "home"}`),
          })}
          href={item.href}
          aria-disabled={item.disabled}
          key={`main-nav-item-${index}`}
        >
          {item.title}
        </Link>
      ))}
    </nav>
  );
}
