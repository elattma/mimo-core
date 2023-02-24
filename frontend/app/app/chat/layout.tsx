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
        <main className="grow bg-red-100">
          <ChatInterface />
        </main>
        <aside className="bg-blue-100 max-lg:h-64 lg:w-96 xl:w-128">
          {children}
        </aside>
      </div>
    </ChatHistoryProvider>
  );
};

export default Layout;
