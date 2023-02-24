import type { NextRequest } from "next/server";

const GET = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development")
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  const searchParams = request.nextUrl.searchParams;
  console.log(searchParams.get("message"));
  return new Response(JSON.stringify({ message: "Hello from chat API" }), {
    status: 200,
    statusText: "OK",
  });
};

export { GET };
