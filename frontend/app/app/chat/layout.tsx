import ChatDisplay from "@/components/chat-display";
import ChatInput from "@/components/chat-input";
import { ChatHistoryProvider } from "@/contexts/chat-history-context";
import { SelectedItemProvider } from "@/contexts/selected-item-context";
import { serverGet } from "@/lib/server-fetchers";
import { getSession as auth0GetSession } from "@auth0/nextjs-auth0";
import { IncomingMessage, ServerResponse } from "http";
import { Socket } from "net";
import { headers } from "next/headers";
import type { ReactNode } from "react";

type ChatLayoutProps = {
  children?: ReactNode;
};

function getReqResp(headers: Headers) {
  const req = new IncomingMessage(new Socket());
  headers.forEach((v, k) => {
    req.headers[k] = v;
  });
  const res = new ServerResponse(req);
  return { req, res };
}

async function getSession(headers: Headers) {
  const { req, res } = getReqResp(headers);
  return { session: await auth0GetSession(req, res), req, res };
}

const ChatLayout = async ({ children }: ChatLayoutProps) => {
  const chatHistoryData = await serverGet("/chat");
  const { session } = await getSession(headers());
  return (
    <ChatHistoryProvider
      initialChatHistory={chatHistoryData}
      accessToken={session?.accessToken || ""}
      userId={session?.user.sub}
    >
      <SelectedItemProvider>
        <div className="container relative flex min-h-0 grow flex-col gap-theme overflow-y-auto pb-theme md:flex-row md:pt-theme">
          <aside className="flex h-fit max-h-64 shrink-0 overflow-hidden rounded-b-theme border-x border-b border-neutral-border p-theme-1/2 md:max-h-full md:w-64 md:shrink-0 md:grow-0 md:flex-col md:border-none lg:w-80">
            {children}
          </aside>
          <main className="relative flex min-h-0 flex-1 flex-col items-center gap-theme-1/4">
            <ChatDisplay />
            <ChatInput />
          </main>
        </div>
      </SelectedItemProvider>
    </ChatHistoryProvider>
  );
};

export default ChatLayout;
