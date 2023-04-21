"use client";

import { useRouter } from "next/navigation";

export default function SettingsPage() {
  const router = useRouter();
  router.push("/dashboard/settings/general");
  return null;
}
