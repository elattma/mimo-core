import { GetEndpoints, PostEndpoints } from "@/types/responses";

const _fetcher = async <JSON = any>(
  input: RequestInfo,
  init?: RequestInit
): Promise<JSON> => {
  const response = await fetch(input, init);

  if (!response.ok) {
    const json = await response.json();
    if (json.error) {
      const error = new Error(json.error) as Error & { status: number };
      error.status = response.status;
      throw error;
    } else {
      throw new Error("An unexpected error occurred");
    }
  }

  return response.json();
};

/**
 * Fetcher for client-side GET requests
 * @param input endpoint (e.g. "/items")
 * @param init request init
 * @returns JSON response as a Promise
 */
export const clientGet = async <Endpoint extends keyof GetEndpoints>(
  input: Endpoint,
  init?: RequestInit
): Promise<GetEndpoints[Endpoint]> => {
  const url = `/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}${input}`;
  return _fetcher(url, {
    method: "GET",
    ...init,
  });
};

/**
 * Fetcher for client-side POST requests
 * @param input endpoint (e.g. "/items")
 * @param init request init
 * @returns JSON response as a Promise
 */
export const clientPost = async <Endpoint extends keyof PostEndpoints>(
  input: Endpoint,
  init?: RequestInit
): Promise<PostEndpoints[Endpoint]> => {
  const url = `/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}${input}`;
  return _fetcher(url, {
    method: "POST",
    ...init,
  });
};
