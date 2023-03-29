import { NextRequest } from "next/server";

const POST = async (request: NextRequest) => {
  if (!request.body) {
    return new Response("Missing body", { status: 400 });
  }
  const data = await request.json();
  if (!data.message) {
    return new Response("Missing message in body", { status: 400 });
  }

  return fetch(process.env.SLACK_WEBHOOK_URL || "", {
    method: "POST",
    body: JSON.stringify({ text: data.message }),
    next: { revalidate: 1 },
  });
};

export { POST };
