"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (router) {
      router.push("/dashboard/home");
    }
  }, [router]);

  return null;
}
