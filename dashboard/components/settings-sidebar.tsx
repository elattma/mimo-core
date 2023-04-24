"use client";

import Link from "next/link";
import { cva } from "class-variance-authority";
import { usePathname } from "next/navigation";

import type { NavItem } from "@/types";

type SettingsSidebarProps = {
  items: NavItem[];
};

export function SettingsSidebar({ items }: SettingsSidebarProps) {
  const pathname = usePathname();

  return items.length ? (
    <div className="flex w-full flex-col">
      {items.map((item, index) => (
        <SettingsSidebarItem
          item={item}
          pathname={pathname}
          key={`settings-sidebar-item-${index}`}
        />
      ))}
    </div>
  ) : null;
}

const settingsSidebarItemVariants = cva(
  "rounded-sm select-none px-2 py-1 hover:bg-accent focus:bg-accent",
  {
    variants: {
      active: {
        true: "underline",
        false: "underline-none",
      },
    },
  }
);

type SettingsSidebarItemProps = {
  item: NavItem;
  pathname: string | null;
};

function SettingsSidebarItem({ item, pathname }: SettingsSidebarItemProps) {
  return (
    <Link
      className={settingsSidebarItemVariants({
        active: pathname === item.href,
      })}
      href={item.href}
      onClick={(event) => {
        event.currentTarget.blur();
      }}
    >
      {item.title}
    </Link>
  );
}
