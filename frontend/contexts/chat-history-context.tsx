"use client";

import { ReactNode, createContext, useContext, useState } from "react";

type User = "mimo" | "user";
type Chat = {
  message: string;
  user: User;
};
type ChatHistory = Chat[];
type ChatHistoryContextType = {
  chatHistory: ChatHistory;
  addToChatHistory: (message: string, user: User) => void;
};

const ChatHistoryContext = createContext<ChatHistoryContextType | undefined>(
  undefined
);

interface Props {
  children: ReactNode;
}

const ChatHistoryProvider = ({ children }: Props) => {
  const [chatHistory, setChatHistory] = useState<ChatHistory>([]);

  const addToChatHistory = (message: string, user: User) => {
    setChatHistory((prev) => [...prev, { message, user }]);
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
export type { Chat };
