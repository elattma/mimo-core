"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { Chat } from "@/models";
import { ArrowDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import AssistantChatItem from "./assistant-chat-item";
import UserChatItem from "./user-chat-item";

function userIsAtBottomOfChat(container: HTMLDivElement) {
  return (
    container.scrollHeight - container.clientHeight - container.scrollTop < 1
  );
}

export default function ChatDisplay() {
  const containerRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const { chatHistory } = useChatHistoryContext();
  const [showArrow, setShowArrow] = useState<boolean>(false);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  return (
    <div
      className="scrollbar-track-hidden overflow-y-overlay flex max-h-full w-full grow flex-col items-center"
      onScroll={(event) => {
        if (userIsAtBottomOfChat(event.currentTarget)) setShowArrow(false);
        else setShowArrow(true);
      }}
    >
      <div className="flex w-full min-w-0 flex-col gap-theme lg:w-[600px] xl:w-[800px]">
        {chatHistory.map((chat, index) => {
          if (chat.role === Chat.Role.ASSISTANT)
            return <AssistantChatItem chat={chat} key={index} />;
          else if (chat.role === Chat.Role.USER)
            return <UserChatItem chat={chat} key={index} />;
        })}
        <div className="h-theme w-full bg-transparent"></div>
        <div ref={chatEndRef} className="h-theme-2 w-full bg-transparent"></div>
        {showArrow && (
          <button
            className="absolute bottom-28 left-0 right-0 mx-auto w-fit rounded-full border border-neutralA-8 bg-neutralA-7 p-theme-1/4"
            onClick={() =>
              chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
            }
          >
            <ArrowDown className="h-4 w-4 text-neutralA-9" />
          </button>
        )}
      </div>
    </div>
  );
}
