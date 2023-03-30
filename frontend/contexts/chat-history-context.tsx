"use client";

import { Chat } from "@/models";
import { GetChatResponse } from "@/types/responses";
import { createContext, ReactNode, useContext, useState } from "react";

type ChatHistoryType = Chat[];
type ChatHistoryContextType = {
  chatHistory: ChatHistoryType;
  addToChatHistory: (chat: Chat) => void;
};

const chatHistoryContext = createContext<ChatHistoryContextType | undefined>(
  undefined
);

type Props = {
  children: ReactNode;
  initialChatHistory: GetChatResponse;
  accessToken: string;
  userId: string;
};

const ChatHistoryProvider = ({ children, initialChatHistory }: Props) => {
  const [chatHistory, setChatHistory] = useState<ChatHistoryType>(
    initialChatHistory?.map((chat) => Chat.fromJSON(chat))
  );

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
  };

  return (
    <chatHistoryContext.Provider value={{ chatHistory, addToChatHistory }}>
      {children}
    </chatHistoryContext.Provider>
  );
};

const useChatHistoryContext = () => {
  const context = useContext(chatHistoryContext);
  if (context === undefined) {
    throw new Error(
      "useChatHistoryContext must be used within a ChatHistoryProvider"
    );
  }
  return context;
};

export { ChatHistoryProvider, useChatHistoryContext };
