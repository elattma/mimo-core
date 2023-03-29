import { DynamoDB } from "@aws-sdk/client-dynamodb";
import { NextRequest } from "next/server";

const POST = async (request: NextRequest) => {
  if (!request.body) {
    return new Response("Missing body", { status: 400 });
  }
  const data = await request.json();
  if (!data.message) {
    return new Response("Missing message in body", { status: 400 });
  }

  const dynamoClient = new DynamoDB({ region: "us-east-1" });
  try {
    await dynamoClient.putItem({
      TableName: "mimo-beta-waitlist",
      Item: {
        email: { S: data.message },
      },
    });
  } catch (e) {
    return new Response("Error saving to dynamo", { status: 500 });
  }

  await fetch(process.env.SLACK_WEBHOOK_URL || "", {
    method: "POST",
    body: JSON.stringify({ text: data.message }),
  });

  return;
};

export { POST };
