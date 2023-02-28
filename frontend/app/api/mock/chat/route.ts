import type { NextRequest } from "next/server";

const GET = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  const response = new Response(
    JSON.stringify(
      [0, 1, 2, 3, 4].map((num) => ({
        parent: "USER#0",
        child: `MESSAGE#${num}`,
        author: "0",
        message: "Test message",
        timestamp: "0",
      }))
    ),
    {
      status: 200,
      statusText: "OK",
    }
  );
  return response;
};

const POST = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  const response = new Response(
    JSON.stringify({ message: "Hello from chat API" }),
    {
      status: 200,
      statusText: "OK",
    }
  );
  return response;
};

export { GET, POST };
