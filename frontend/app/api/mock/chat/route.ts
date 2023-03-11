import { mock_logRequest, mock_logResponse } from "@/lib/logs";
import { awaitTimeout } from "@/lib/util";
import { Chat } from "@/models";
import type { NextRequest } from "next/server";
import { ulid } from "ulid";

const RANDOM_WORDS = [
  "loyalty",
  "environmental",
  "state",
  "extent",
  "desire",
  "spontaneous",
  "building",
  "gallery",
  "broken",
  "interactive",
  "convict",
  "shame",
  "charter",
  "gate",
  "figure",
  "consumption",
  "desert",
  "houseplant",
  "tail",
  "government",
  "temptation",
  "favor",
  "log",
  "practical",
  "disaster",
  "crisis",
  "cute",
  "consider",
  "clue",
  "support",
  "voter",
  "galaxy",
  "campaign",
  "worth",
  "fund",
  "band",
  "closed",
  "descent",
  "hut",
  "if",
  "revoke",
  "rebel",
  "follow",
  "form",
  "slippery",
  "coach",
  "rake",
  "makeup",
  "pastel",
  "football",
];

const GET = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  mock_logRequest(request);
  const response = new Response(
    JSON.stringify(
      [0, 1, 2, 3, 4, 5].map((num) => {
        const randomLength = Math.floor(Math.random() * 20) + 1;
        const randomWords = Array.from(
          { length: randomLength },
          () => RANDOM_WORDS[Math.floor(Math.random() * RANDOM_WORDS.length)]
        );
        return {
          id: ulid(),
          message: randomWords.join(" "),
          author: ulid(),
          role: num % 2 === 0 ? Chat.Role.USER : Chat.Role.ASSISTANT,
          timestamp: Date.now(),
        };
      })
    ),
    {
      status: 200,
      statusText: "OK",
    }
  );
  mock_logResponse(response);
  return response;
};

const POST = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  mock_logRequest(request);
  if (!request.body) {
    return new Response(null, {
      status: 400,
      statusText: "Invalid or missing request body",
    });
  }
  const randomLength = Math.floor(Math.random() * 20) + 1;
  const randomWords = Array.from(
    { length: randomLength },
    () => RANDOM_WORDS[Math.floor(Math.random() * RANDOM_WORDS.length)]
  );
  const response = new Response(
    JSON.stringify({
      id: ulid(),
      message: randomWords.join(" "),
      author: ulid(),
      role: Chat.Role.ASSISTANT,
      timestamp: Date.now(),
    }),
    {
      status: 200,
      statusText: "OK",
    }
  );
  mock_logResponse(response);
  await awaitTimeout(1000);
  return response;
};

export { GET, POST };
