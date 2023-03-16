"use client";

import { LoadingDots } from "@/components/ui/loading-dots";
import { clientPost } from "@/lib/client-fetchers";
import { useRouter, useSearchParams } from "next/navigation";

const Page = () => {
  const searchParams = useSearchParams();
  const router = useRouter();

  if (searchParams && searchParams.has("code") && searchParams.has("state")) {
    const state = JSON.parse(
      Buffer.from(searchParams.get("state") as string, "base64").toString(
        "utf-8"
      )
    );
    clientPost("/integration", {
      body: JSON.stringify({
        id: state.integrationId,
        code: searchParams.get("code"),
        redirect_uri: `${process.env.NEXT_PUBLIC_BASE_URL}/auth`,
      }),
    }).then(() => router.push("/app/integrations"));
  } else if (searchParams && searchParams.has("error")) {
    // TODO: Proper error handling here
    console.error(searchParams.get("error"));
  } else {
    // TODO: Proper error handling here too
  }

  return (
    <div className="flex grow items-center justify-center">
      <LoadingDots />
    </div>
  );
};

export default Page;
