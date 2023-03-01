"use client";

import { fetcher } from "@/lib/utils";
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
    fetcher(`/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}/integration`, {
      method: "POST",
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

  return <>Auth</>;
};

export default Page;
