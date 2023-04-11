"use client";

import AssistantThought from "@/components/assistant-thought";
import { ScrollArea } from "@/components/ui/scroll-area";
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
  const chatEndRef = useRef<HTMLDivElement>(null);
  const { chatHistory, thoughts } = useChatHistoryContext();
  const [showArrow, setShowArrow] = useState<boolean>(false);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, thoughts]);

  return (
    <ScrollArea
      className="relative flex w-full flex-1 flex-col items-center"
      innerClassName="w-fit"
      onScroll={(event) => {
        if (userIsAtBottomOfChat(event.currentTarget)) setShowArrow(false);
        else setShowArrow(true);
      }}
    >
      <div className="flex w-full min-w-0 flex-col gap-theme lg:w-[600px] xl:w-[800px]">
        {chatHistory.map((chat, index) => {
          if (chat.role === Chat.Role.ASSISTANT) {
            const displayThoughts = index === chatHistory.length - 1;
            return (
              <>
                {displayThoughts
                  ? thoughts.map((thought, thoughtIndex) => (
                      <AssistantThought
                        thought={thought}
                        key={`thought-${thoughtIndex}`}
                      />
                    ))
                  : null}
                <AssistantChatItem chat={chat} key={index} />
              </>
            );
          } else if (chat.role === Chat.Role.USER)
            return <UserChatItem chat={chat} key={index} />;
        })}
        {chatHistory.length > 0 &&
        chatHistory[chatHistory.length - 1].role !== Chat.Role.ASSISTANT
          ? thoughts.map((thought, index) => (
              <AssistantThought thought={thought} key={`thought-${index}`} />
            ))
          : null}
        <div ref={chatEndRef} />
      </div>
      {showArrow && (
        <button
          className="absolute bottom-0 left-0 right-0 mx-auto w-fit rounded-full border border-neutralA-8 bg-neutralA-6 p-theme-1/4"
          aria-label="Scroll to bottom"
          onClick={() =>
            chatEndRef.current?.scrollIntoView({ behavior: "smooth" })
          }
        >
          <ArrowDown className="h-3 w-3 text-neutralA-9" />
        </button>
      )}
    </ScrollArea>
  );
}
