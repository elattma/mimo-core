import type { NextRequest } from "next/server";

const GET = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  const response = new Response(
    JSON.stringify([
      {
        source: "drive",
        type: "doc",
        title: "Test Document",
        preview:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor",
      },
      {
        source: "drive",
        type: "doc",
        title: "Test Document",
        preview:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor",
      },
      {
        source: "drive",
        type: "doc",
        title: "Test Document",
        preview:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor",
      },
      {
        source: "drive",
        type: "doc",
        title: "Test Document",
        preview:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor",
      },
      {
        source: "drive",
        type: "doc",
        title: "Test Document",
        preview:
          "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor",
      },
    ]),
    {
      status: 200,
      statusText: "OK",
    }
  );
  const origin = request.headers.get("origin");
  if (origin !== null && origin.match(/(\.|^)localhost:3000$/)) {
    response.headers.set("Access-Control-Allow-Origin", origin);
    response.headers.set(
      "Access-Control-Allow-Headers",
      "X-Requested-With,Content-Type"
    );
    response.headers.set("Access-Control-Allow-Methods", "GET");
  }
  return response;
};

export { GET };
