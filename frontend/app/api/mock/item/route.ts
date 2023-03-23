import { mock_logRequest, mock_logResponse } from "@/lib/logs";
import type { NextRequest } from "next/server";
import { ulid } from "ulid";

const GET_ITEMS_COUNT = 5;

const GET = async (request: NextRequest) => {
  mock_logRequest(request);
  const response = new Response(
    JSON.stringify([
      {
        integration: "google",
        icon: "https://www.gstatic.com/images/branding/product/1x/drive_512dp.png",
        items: Array(GET_ITEMS_COUNT).fill({
          id: ulid(),
          title: "Mock Item Title",
          link: "https://www.mimo.team",
          preview: "Mock item preview",
        }),
      },
    ]),
    {
      status: 200,
      statusText: "OK",
    }
  );
  mock_logResponse(response);
  return response;
};

const POST = async (request: NextRequest) => {
  mock_logRequest(request);
  const response = new Response(
    JSON.stringify({
      signedUrl: "https://www.signedurl.com",
    }),
    { status: 200, statusText: "OK" }
  );
  mock_logResponse(response);
  return response;
};

export { GET, POST };
