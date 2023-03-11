"use client";

import { Chat } from "@/models";
import { GetChatResponse } from "@/types/responses";
import { ReactNode, createContext, useContext, useState } from "react";

type ChatHistoryType = Chat[];
type ChatHistoryContextType = {
  chatHistory: ChatHistoryType;
  addToChatHistory: (chat: Chat) => void;
};

const ChatHistoryContext = createContext<ChatHistoryContextType | undefined>(
  undefined
);

type Props = {
  children: ReactNode;
  initialChatHistory: GetChatResponse;
};

const ChatHistoryProvider = ({ children, initialChatHistory }: Props) => {
  const [chatHistory, setChatHistory] = useState<ChatHistoryType>(
    initialChatHistory.map((chat) => Chat.fromJSON(chat))
  );

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
  };

  return (
    <ChatHistoryContext.Provider value={{ chatHistory, addToChatHistory }}>
      {children}
    </ChatHistoryContext.Provider>
  );
};

const useChatHistoryContext = () => {
  const context = useContext(ChatHistoryContext);
  if (context === undefined) {
    throw new Error("Expected chatHistory to be defined.");
  }
  return context;
};

export { ChatHistoryProvider, useChatHistoryContext };
