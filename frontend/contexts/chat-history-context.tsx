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

const THOUGHT_PREFIX = "[THOUGHT]";

type ChatHistoryType = Chat[];
type ThoughtsType = string[];
type ChatHistoryContextType = {
  chatHistory: ChatHistoryType;
  addToChatHistory: (chat: Chat) => void;
  thoughts: ThoughtsType;
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
  const [thoughts, setThoughts] = useState<ThoughtsType>([]);

  const [client, setClient] = useState<ApolloClient<NormalizedCacheObject>>();

  const isThought = (s: string): boolean => s.startsWith(THOUGHT_PREFIX);

  const extractThought = (s: string): string =>
    s.substring(THOUGHT_PREFIX.length);

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
    if (chat.role === Chat.Role.USER) {
      setThoughts([]);
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
            console.log(updatedChat);
            if (isThought(updatedChat.message)) {
              const thought = extractThought(updatedChat.message);
              console.log("New thought:");
              console.log(updatedChat.message);
              setThoughts((prevThoughts) => [...prevThoughts, thought]);
            } else {
              setChatHistory((prevChatHistory) => {
                const newChat = Chat.fromJSON({
                  message: updatedChat.message,
                  author: "gpt-4",
                  id: updatedChat.outputChatId,
                  timestamp: updatedChat.timestamp,
                  role: Chat.Role.ASSISTANT,
                });
                return [...prevChatHistory, newChat];
              });
            }
          },
        });
    }
  };

  useEffect(() => {
    if (userId && accessToken) {
      const client = getSubscribeClient(accessToken);
      setClient(client);
    }
  }, [userId, accessToken]);

  useEffect(() => {
    console.log("Thoughts:");
    console.log(thoughts);
  }, [thoughts]);

  return (
    <chatHistoryContext.Provider
      value={{ chatHistory, addToChatHistory, thoughts }}
    >
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
