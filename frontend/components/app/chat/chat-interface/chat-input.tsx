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
    fetcher(`/api/mock/chat?message=${message}`).then((data) =>
      addToChatHistory(data.message, "mimo")
    );
    setMessage("");
  };

  return (
    <form onSubmit={handleSubmit} autoComplete="off">
      <input
        type="text"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
      />
      <button type="submit">Send</button>
    </form>
  );
};

export default ChatInput;
