import { getSession, withApiAuthRequired } from "@auth0/nextjs-auth0";
import type { NextApiRequest, NextApiResponse } from "next";

const handler = async (request: NextApiRequest, response: NextApiResponse) => {
  // Get the session
  const session = await getSession(request, response);
  if (!session || !session.accessToken) {
    return response
      .status(401)
      .json({ error: "Not authenticated; session not set." });
  }

  // Reform the URL
  const { slug, ...query } = request.query;
  if (slug === undefined || typeof slug === "string")
    return response.status(400).json({ error: "Malformed slug." });
  const url = new URL(`https://api.mimo.team/${slug.join("/")}`);
  if (typeof query === "object") {
    Object.entries(query).forEach(([key, value]) => {
      url.searchParams.set(key, value as string);
    });
  } else {
    return response
      .status(400)
      .json({ error: "Endpoint formatted incorrectly." });
  }

  // Log request
  if (process.env.NODE_ENV === "development") {
    const now = new Date();
    console.log(
      `Request received at ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`
    );
    console.log("Request URL:", request.url);
    console.log("Request method:", request.method);
    console.log("Request headers:", request.headers);
    console.log("Request body:", request.body);
    console.log(`\nAttempting to forward response to ${url.toString()}...\n`);
  }

  try {
    // Forward the request
    const responseToForward = await fetch(url.toString(), {
      method: request.method,
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
        "x-api-key": process.env.API_KEY,
      },
      ...(request.body && { body: request.body }),
    });
    const dataToForward = await responseToForward.json();

    // Log response
    if (process.env.NODE_ENV === "development") {
      const now = new Date();
      console.log(
        `Response received at ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`
      );
      console.log("Response status:", responseToForward.status);
      console.log("Response data:", dataToForward);
    }

    // Forward the status and json data
    return response.status(responseToForward.status).json(dataToForward);
  } catch (error) {
    if (process.env.NODE_ENV === "development") {
      console.log(error);
    }
    return response.status(500).json({ error: error });
  }
};

export default withApiAuthRequired(handler);
