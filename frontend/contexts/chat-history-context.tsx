"use client";

import getSubscribeClient from "@/lib/subscribe-client";
import { Chat } from "@/models";
import { GetChatResponse } from "@/types/responses";
import {
  ApolloClient,
  gql,
  NormalizedCacheObject,
  useSubscription,
} from "@apollo/client";
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
  const [client, setClient] = useState<ApolloClient<NormalizedCacheObject>>(
    getSubscribeClient(accessToken)
  );
  const [token, setToken] = useState<string>(accessToken);
  const [latestUserChat, setLatestUserChat] = useState<Chat | null>(
    new Chat("random", "me")
  );
  const [chatHistory, setChatHistory] = useState<ChatHistoryType>(
    initialChatHistory.map((chat) => Chat.fromJSON(chat))
  );

  const { data: newChat, loading: newChatLoading } = useSubscription(
    AddedChat,
    {
      variables: { userId: userId || "", inputChatId: latestUserChat?.id },
      client: client,
    }
  );

  useEffect(() => {
    if (token !== accessToken) {
      setClient(getSubscribeClient(accessToken));
      setToken(accessToken);
    }
  }, [accessToken]);

  useEffect(() => {
    if (
      !newChatLoading &&
      newChat &&
      newChat.inputChatId &&
      newChat.outputChatId
    ) {
      if (chatHistory?.length < 1) throw Error("Chat history is empty.");

      const newChatObject = Chat.fromJSON({
        message: newChat.message,
        author: newChat.role,
        id: newChat.outputChatId,
        timestamp: newChat.timestamp,
        role: newChat.role,
      });
      setChatHistory((prev) => [...prev, newChatObject]);
    }
  }, [newChat, newChatLoading]);

  const addToChatHistory = (chat: Chat) => {
    setChatHistory((prev) => [...prev, chat]);
    if (chat.role === Chat.Role.USER) setLatestUserChat(chat);
    else setLatestUserChat(null);
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
