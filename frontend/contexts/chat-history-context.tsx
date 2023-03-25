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

const AddedChat = gql`
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
`;

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
  accessToken: string;
  userId: string;
};

const ChatHistoryProvider = ({
  children,
  initialChatHistory,
  accessToken,
  userId,
}: Props) => {
  const [client, setClient] =
    useState<ApolloClient<NormalizedCacheObject> | null>(null);
  useEffect(() => {
    if (accessToken) {
      const newClient = getSubscribeClient(accessToken);
      setClient(newClient);
    }
  }, [accessToken]);

  const [subscription, setSubscription] = useState<any>(null);
  const [chatHistory, setChatHistory] = useState<ChatHistoryType>(
    initialChatHistory?.map((chat) => Chat.fromJSON(chat))
  );
  const [latestUserChat, setLatestUserChat] = useState<Chat | null>(
    chatHistory?.[chatHistory.length - 1] || new Chat("message", "author")
  );

  useEffect(() => {
    if (client && userId && latestUserChat) {
      console.log("hi!!");
      console.log(userId);
      console.log(latestUserChat.id);
      const clientSubscription = client
        .subscribe({
          query: AddedChat,
          variables: {
            userId: userId,
            inputChatId: latestUserChat.id,
          },
        })
        .subscribe(
          (next) => {
            console.log(next);
          },
          (error) => {
            console.log(error);
          },
          () => {
            console.log("completed");
          }
        );

      console.log(clientSubscription);
      setSubscription(clientSubscription);
    }
  }, [client, latestUserChat]);

  // useEffect(() => {
  //   if (
  //     !newChatLoading &&
  //     newChat &&
  //     newChat.inputChatId &&
  //     newChat.outputChatId
  //   ) {
  //     if (chatHistory?.length < 1) throw Error("Chat history is empty.");

  //     const newChatObject = Chat.fromJSON({
  //       message: newChat.message,
  //       author: newChat.role,
  //       id: newChat.outputChatId,
  //       timestamp: newChat.timestamp,
  //       role: newChat.role,
  //     });
  //     setChatHistory((prev) => [...prev, newChatObject]);
  //   }
  // }, [newChat, newChatLoading]);

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
    if (chat.role === Chat.Role.USER) setLatestUserChat(chat);
    else setLatestUserChat(null);
  };
  console.log(chatHistory);

  return (
    <ChatHistoryContext.Provider value={{ chatHistory, addToChatHistory }}>
      {children}
    </ChatHistoryContext.Provider>
  );
};

const useChatHistoryContext = () => {
  const context = useContext(ChatHistoryContext);
  if (context === undefined) {
    throw new Error(
      "useChatHistoryContext must be used within a ChatHistoryProvider"
    );
  }
  return context;
};

export { ChatHistoryProvider, useChatHistoryContext };
