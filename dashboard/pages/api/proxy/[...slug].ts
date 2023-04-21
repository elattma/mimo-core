import {
  getSession,
  updateSession,
  withApiAuthRequired,
} from "@auth0/nextjs-auth0";
import type { NextApiRequest, NextApiResponse } from "next";

const handler = async (request: NextApiRequest, response: NextApiResponse) => {
  const session = await getSession(request, response);
  if (!session || !session.accessToken) {
    return response
      .status(401)
      .json({ error: "Not authenticated; session not set." });
  }

  if (
    session.accessTokenExpiresAt &&
    session.accessTokenExpiresAt < Date.now() / 1000
  ) {
    const refreshResponse = await fetch(
      `${process.env.AUTH0_ISSUER_BASE_URL}/oauth/token`,
      {
        method: "POST",
        body: JSON.stringify({
          grant_type: "refresh_token",
          client_id: process.env.AUTH0_CLIENT_ID,
          client_secret: process.env.AUTH0_CLIENT_SECRET,
          refresh_token: session.refreshToken,
        }),
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    const refreshSession = await refreshResponse.json();
    updateSession(request, response, refreshSession);
  }

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

  try {
    const responseToForward = await fetch(url.toString(), {
      method: request.method,
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
      },
      ...(request.body && { body: request.body }),
    });
    const dataToForward = await responseToForward.json();

    return response.status(responseToForward.status).json(dataToForward);
  } catch (error) {
    return response.status(500).json({ error: error });
  }
};

export default withApiAuthRequired(handler);
