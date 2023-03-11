"use client";

import { cn } from "@/lib/util";
import Link from "next/link";
import { useSelectedLayoutSegment } from "next/navigation";

type MainNavProps = {
  items?: {
    title: string;
    href: string;
  }[];
};

export default function MainNav({ items }: MainNavProps) {
  const segment = useSelectedLayoutSegment();

  return (
    <nav className="flex gap-theme-1/2 md:gap-theme">
      {items?.map((item, index) => (
        <Link
          className={cn(
            "rounded-theme px-theme-1/4 py-theme-1/8 text-sm font-semibold",
            item.href.startsWith(`/app/${segment}`)
              ? "bg-brand-bg text-brand-text"
              : "bg-neutral-bg text-neutral-text"
          )}
          href={item.href}
          key={index}
        >
          {item.title}
        </Link>
      ))}
    </nav>
  );
}
