import ChatDisplay from "@/components/chat-display";
import ChatInput from "@/components/chat-input";
import { ChatHistoryProvider } from "@/contexts/chat-history-context";
import { serverGet } from "@/lib/server-fetchers";
import type { ReactNode } from "react";

type ChatLayoutProps = {
  children?: ReactNode;
};

const ChatLayout = async ({ children }: ChatLayoutProps) => {
  const chatHistoryData = await serverGet("/chat");

  return (
    <ChatHistoryProvider initialChatHistory={chatHistoryData}>
      <div className="container flex min-h-0 grow flex-col gap-theme pb-theme md:flex-row">
        <aside className="flex h-64 w-full shrink-0 sm:w-64 md:h-fit md:flex-col lg:w-80">
          {children}
        </aside>
        <main className="relative flex w-full min-w-0 grow-0 flex-col">
          <ChatDisplay />
          <div className="relative mb-theme flex w-full max-w-full grow-0 items-center justify-center">
            <ChatInput />
          </div>
        </main>
      </div>
    </ChatHistoryProvider>
  );
};

export default ChatLayout;
