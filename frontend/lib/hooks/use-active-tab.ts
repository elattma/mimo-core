"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

type Tab = "chat" | "integrations";
const LOOKUP: Record<Tab, boolean> = {
  chat: true,
  integrations: true,
};

const getActiveTab = (pathname: string): Tab | null => {
  const segments = pathname.split("/");
  if (segments.length > 2 && LOOKUP[segments[2] as Tab])
    return segments[2] as Tab;
  return null;
};

const useActiveTab = () => {
  const pathname = usePathname();
  const [activeTab, setActiveTab] = useState<Tab | null>(null);

  useEffect(
    () => setActiveTab(pathname === null ? null : getActiveTab(pathname)),
    [pathname]
  );

  return activeTab;
};

export default useActiveTab;
