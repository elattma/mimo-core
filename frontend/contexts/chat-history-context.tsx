"use client";

import { getSubscribeClient } from "@/lib/subscribe-client";
import { Chat } from "@/models";
import { GetChatResponse } from "@/types/responses";
import { ApolloClient, gql, NormalizedCacheObject } from "@apollo/client";
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
  const [client, setClient] = useState<ApolloClient<NormalizedCacheObject>>();

  useEffect(() => {
    if (userId && accessToken) {
      const client = getSubscribeClient(accessToken);
      setClient(client);
    }
  }, [userId, accessToken]);

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
    if (chat.role === Chat.Role.USER) {
      client
        ?.subscribe({
          query: AddedChat,
          variables: {
            userId,
            inputChatId: chat.id,
          },
        })
        .subscribe({
          next: (result) => {
            const updatedChat = result.data.updatedChat;
            setChatHistory((prev) => {
              const updatedChatIndex = prev.findIndex(
                (chat) => chat.id === updatedChat.outputChatId
              );
              if (updatedChatIndex === -1) {
                return [
                  ...prev,
                  Chat.fromJSON({
                    message: updatedChat.message,
                    author: "gpt-4",
                    id: updatedChat.outputChatId,
                    timestamp: updatedChat.timestamp,
                    role: Chat.Role.ASSISTANT,
                  }),
                ];
              }
              const updatedChatHistory = [...prev];
              updatedChatHistory[updatedChatIndex] = Chat.fromJSON({
                message: updatedChat.message,
                author: "gpt-4",
                id: updatedChat.outputChatId,
                timestamp: updatedChat.timestamp,
                role: Chat.Role.ASSISTANT,
              });
              return updatedChatHistory;
            });
          },
        });
    }
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
