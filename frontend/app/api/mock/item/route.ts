import { mock_logRequest, mock_logResponse } from "@/lib/logs";
import type { NextRequest } from "next/server";
import { ulid } from "ulid";

const INTEGRATED_ITEMS_COUNT = 10;
const UPLOADED_ITEMS_COUNT = 10;

const GET = async (request: NextRequest) => {
  mock_logRequest(request);
  const mockIntegratedItem = {
    integration: "google",
    id: ulid(),
    title: "Mock Integrated Item Title",
    icon: "www.gstatic.com/images/branding/product/1x/drive_512dp.png",
    link: "https://www.mimo.team",
  };
  const mockUploadedItem = {
    integration: "upload",
    id: ulid(),
    title: "Mock Uploaded Item Title",
    link: "https://www.mimo.team",
  };
  const items = Array(INTEGRATED_ITEMS_COUNT + UPLOADED_ITEMS_COUNT)
    .fill(mockIntegratedItem)
    .fill(mockUploadedItem, INTEGRATED_ITEMS_COUNT);
  const response = new Response(
    JSON.stringify({
      items,
      next_token: "MOCK_NEXT_TOKEN",
    }),
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
