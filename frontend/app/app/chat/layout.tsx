import ChatInterface from "@/components/app/chat/chat-interface";
import { ChatHistoryProvider } from "@/contexts/chat-history-context";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

const Layout = ({ children }: Props) => {
  return (
    <ChatHistoryProvider>
      <div className="flex h-full w-full flex-col-reverse lg:flex-row">
        <main className="grow">
          <ChatInterface />
        </main>
        <aside className="shrink-0 border-solid border-neutral-border max-lg:h-64 max-lg:border-b lg:w-96 lg:border-l xl:w-128">
          {children}
        </aside>
      </div>
    </ChatHistoryProvider>
  );
};

export default Layout;
