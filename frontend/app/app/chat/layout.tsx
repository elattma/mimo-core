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
      <div className="container relative flex min-h-0 grow flex-col gap-theme pb-theme md:flex-row md:pt-theme">
        <aside className="flex h-fit max-h-64 shrink-0 overflow-hidden rounded-b-theme border-x border-b border-neutral-border p-theme-1/2 md:max-h-full md:w-64 md:shrink-0 md:grow-0 md:flex-col md:border-none lg:w-80">
          {children}
        </aside>
        <main className="relative flex min-h-0 flex-1 flex-col items-center gap-theme-1/4">
          <ChatDisplay />
          <ChatInput />
        </main>
      </div>
    </ChatHistoryProvider>
  );
};

export default ChatLayout;
