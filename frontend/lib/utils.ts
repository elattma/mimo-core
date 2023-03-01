/**
 * A wrapper around fetch that throws an error if the response is not ok
 * and parses the response as JSON.
 *
 * @param input endpoint to fetch from
 * @param init configuration for the request
 * @returns The JSON response from the server
 */
export const fetcher = async <JSON = any>(
  input: RequestInfo,
  init?: RequestInit
): Promise<JSON> => {
  const res = await fetch(input, init);

  if (!res.ok) {
    const json = await res.json();
    if (json.error) {
      const error = new Error(json.error) as Error & { status: number };
      error.status = res.status;
      throw error;
    } else {
      throw new Error("An unexpected error occurred");
    }
  }

  return res.json();
};
