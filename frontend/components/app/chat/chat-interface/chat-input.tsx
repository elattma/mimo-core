"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { fetcher } from "@/lib/utils";
import { FormEventHandler, useState } from "react";

const ChatInput = () => {
  const { addToChatHistory } = useChatHistoryContext();
  const [message, setMessage] = useState("");

  const handleSubmit: FormEventHandler = (event) => {
    event.preventDefault();
    addToChatHistory(message, "user");
    fetcher(
      `http://localhost:3000/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}/chat?message=${message}`,
      {
        method: "GET",
      }
    ).then((data) => addToChatHistory(data.message, "mimo"));
    setMessage("");
  };

  return (
    <div className="flex w-full items-center justify-center border-t border-neutral-border py-6">
      <form
        className="relative h-fit w-4/5"
        onSubmit={handleSubmit}
        autoComplete="off"
      >
        <textarea
          className="h-full w-full bg-brand-bg p-3"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />
        <button
          className="absolute right-0 bottom-0 bg-brand-solid text-brand-on-solid"
          type="submit"
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
