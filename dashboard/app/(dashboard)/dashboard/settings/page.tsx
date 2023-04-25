"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function SettingsPage() {
  const router = useRouter();
  useEffect(() => {
    if (router) {
      router.push("/dashboard/settings/general");
    }
  }, [router]);
  return null;
}
