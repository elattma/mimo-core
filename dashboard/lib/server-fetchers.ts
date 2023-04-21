import { GetEndpoints, PostEndpoints } from "@/types/responses";
import { cookies } from "next/headers";

const _fetcher = async <JSON = any>(
  input: RequestInfo,
  init?: RequestInit
): Promise<JSON> => {
  const sessionCookie = cookies().get("appSession");
  if (!sessionCookie) {
    throw new Error("Failed to get session cookie");
  }

  const response = await fetch(
    input,
    init
      ? {
          ...init,
          headers: {
            ...init.headers,
            cookie: `appSession=${sessionCookie.value}`,
          },
        }
      : { headers: { cookie: `appSession=${sessionCookie.value}` } }
  );

  if (!response.ok) {
    const json = await response.json();
    if (json.error) {
      const error = new Error(json.error) as Error & { status: number };
      error.status = response.status;
      throw error;
    } else {
      console.log(json);
      throw new Error("An unexpected error occurred");
    }
  }

  return response.json();
};

/**
 * Fetcher for server-side GET requests
 * @param input endpoint (e.g. "/items")
 * @param init request init
 * @returns JSON response as a Promise
 */
export const serverGet = async <Endpoint extends keyof GetEndpoints>(
  input: Endpoint,
  init?: RequestInit
): Promise<GetEndpoints[Endpoint]> => {
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/api/proxy${String(input)}`;
  return _fetcher(url, {
    method: "GET",
    ...init,
  });
};

/**
 * Fetcher for server-side POST requests
 * @param input endpoint (e.g. "/items")
 * @param init request init
 * @returns JSON response as a Promise
 */
export const serverPost = async <Endpoint extends keyof PostEndpoints>(
  input: Endpoint,
  init?: RequestInit
): Promise<PostEndpoints[Endpoint]> => {
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/api/proxy${String(input)}`;
  return _fetcher(url, {
    method: "POST",
    ...init,
  });
};
