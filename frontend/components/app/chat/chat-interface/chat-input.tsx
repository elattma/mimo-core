"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { fetcher } from "@/lib/utils";
import { Send } from "lucide-react";
import { FormEventHandler, useRef, useState } from "react";
import TextareaAutosize from "react-textarea-autosize";

const ChatInput = () => {
  const sendButtonRef = useRef<HTMLButtonElement>(null);
  const { addToChatHistory } = useChatHistoryContext();
  const [message, setMessage] = useState("");

  const handleSubmit: FormEventHandler = (event) => {
    event.preventDefault();
    // TODO: Prevent user from sending empty messages
    // TODO: Prevent user from sending messages when mimo has not responded yet
    addToChatHistory(message.trim(), "user");
    fetcher(
      `http://localhost:3000/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}/chat`,
      {
        method: "POST",
        body: JSON.stringify({ message: message.trim() }),
      }
    ).then((data) => addToChatHistory(data.message.trim(), "mimo"));
    setMessage("");
  };

  return (
    <div className="flex w-full items-center justify-center py-6">
      <form
        className="relative h-fit w-4/5 overflow-hidden rounded-theme border border-neutral-border shadow-md transition-all focus-within:border-neutral-border-hover focus-within:ring focus-within:ring-neutral-border"
        onSubmit={handleSubmit}
        autoComplete="off"
      >
        <TextareaAutosize
          className="w-full resize-none bg-transparent py-3 pl-3 pr-12 outline-none"
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
    </div>
  );
};

export default ChatInput;
