import { cookies } from "next/headers";
import { fetcher } from "./utils";

/**
 * A wrapper around fetcher that adds the session cookie to the request.
 * For use with server-side rendering.
 *
 * @param input endpoint to fetch from
 * @param init configuration for the request
 * @returns The JSON response from the server
 */
export const fetcherWithSession = <JSON = any>(
  input: RequestInfo,
  init?: RequestInit
): Promise<JSON> => {
  const sessionCookie = cookies().get("appSession");
  if (!sessionCookie) {
    throw new Error("Failed to get session cookie");
  }
  return fetcher(
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
};
