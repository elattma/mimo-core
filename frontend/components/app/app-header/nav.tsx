"use client";

import useActiveTab from "@/lib/hooks/use-active-tab";
import Link from "next/link";

const NAV_ITEMS = [
  { label: "Chat", tabId: "chat", href: "/app/chat" },
  { label: "Integrations", tabId: "integrations", href: "/app/integrations" },
];

const Nav = () => {
  const activeTab = useActiveTab();

  return (
    <nav className="flex items-center space-x-theme-1/2">
      {NAV_ITEMS.map((item, index) => (
        <Link
          className={[
            "rounded-theme px-theme-1/4 py-theme-1/8 text-sm font-medium transition-colors",
            activeTab === item.tabId
              ? "bg-brand-bg text-brand-text"
              : "bg-neutral-bg text-neutral-text",
          ].join(" ")}
          href={item.href}
          key={`nav-item-${index}`}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
};

export default Nav;
