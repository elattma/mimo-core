"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { clientPost } from "@/lib/client-fetchers";
import { Chat } from "@/models";
import { useUser } from "@auth0/nextjs-auth0/client";
import { Send } from "lucide-react";
import { FormEventHandler, useRef, useState } from "react";
import TextareaAutosize from "react-textarea-autosize";

export default function ChatInput() {
  const user = useUser();
  const { addToChatHistory } = useChatHistoryContext();
  const sendButtonRef = useRef<HTMLButtonElement>(null);
  const [message, setMessage] = useState("");

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const trimmedMessage = message.trim();
    if (trimmedMessage === "") return;
    if (!user.user?.sub) throw new Error("User is not logged in");
    const chat = new Chat(trimmedMessage, user?.user?.sub);
    addToChatHistory(chat);
    clientPost("/chat", { body: JSON.stringify({ chat: chat.toJSON() }) }).then(
      (data) => addToChatHistory(Chat.fromJSON(data))
    );
    setMessage("");
  };

  return (
    <form
      className="relative h-fit w-full rounded-theme lg:w-fit"
      onSubmit={handleSubmit}
      autoComplete="off"
    >
      <TextareaAutosize
        className="scrollbar-track-hidden w-full resize-none rounded-theme border border-neutralA-3 bg-neutral-base py-theme-1/2 pl-theme-1/2 pr-theme-3/2 text-gray-text-contrast shadow-2xl outline-none lg:w-[600px] xl:w-[800px]"
        minRows={2}
        maxRows={5}
        placeholder="Ask me anything..."
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendButtonRef.current?.click();
          }
        }}
      />
      <button
        ref={sendButtonRef}
        className="absolute right-0 bottom-0 mb-3 mr-3 text-gray-text"
        type="submit"
      >
        <Send width={20} height={20} />
      </button>
    </form>
  );
}
