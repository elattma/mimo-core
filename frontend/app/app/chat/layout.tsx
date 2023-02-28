import ChatInterface from "@/components/app/chat/chat-interface";
import ChatSidebarHeader from "@/components/app/chat/chat-sidebar-header";
import { ChatHistoryProvider } from "@/contexts/chat-history-context";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

const Layout = ({ children }: Props) => {
  return (
    <ChatHistoryProvider>
      <div className="flex h-full w-full flex-col-reverse lg:flex-row">
        <main className="grow lg:w-[calc(100%_-_20rem)] xl:w-[calc(100%_-_32rem)]">
          <ChatInterface />
        </main>
        <aside className="shrink-0 space-y-theme border-solid border-neutral-border p-theme-1/2 max-lg:h-64 max-lg:border-b lg:w-80 lg:border-l xl:w-96">
          <ChatSidebarHeader />
          {children}
        </aside>
      </div>
    </ChatHistoryProvider>
  );
};

export default Layout;
