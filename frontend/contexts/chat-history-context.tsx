"use client";

import { getSubscribeClient } from "@/lib/subscribe-client";
import { Chat } from "@/models";
import { GetChatResponse } from "@/types/responses";
import { gql } from "@apollo/client";
import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";

type ChatHistoryType = Chat[];
type ChatHistoryContextType = {
  chatHistory: ChatHistoryType;
  addToChatHistory: (chat: Chat) => void;
};

const AddedChat = gql(`
  subscription ($userId: ID!, $inputChatId: ID!) {
    updatedChat(userId: $userId, inputChatId: $inputChatId) {
      userId
      inputChatId
      outputChatId
      message
      is_progress
      role
      timestamp
    }
  }
`);

const chatHistoryContext = createContext<ChatHistoryContextType | undefined>(
  undefined
);

type Props = {
  children: ReactNode;
  initialChatHistory: GetChatResponse;
  accessToken: string;
  userId: string;
};

const ChatHistoryProvider = ({
  children,
  initialChatHistory,
  accessToken,
  userId,
}: Props) => {
  const [chatHistory, setChatHistory] = useState<ChatHistoryType>(
    initialChatHistory?.map((chat) => Chat.fromJSON(chat))
  );

  useEffect(() => {
    console.log("???????");
    console.log(accessToken);
    if (accessToken) {
      const client = getSubscribeClient(accessToken);
      console.log(client);
      client.subscribe({
        query: AddedChat,
        variables: {
          userId,
          inputChatId: initialChatHistory[initialChatHistory.length - 1].id,
        },
      });
    }
  }, [accessToken]);

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
