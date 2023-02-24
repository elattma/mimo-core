"use client";

import { Chat, useChatHistoryContext } from "@/contexts/chat-history-context";

const ChatHistory = () => {
  const { chatHistory } = useChatHistoryContext();
  return (
    <div className="w-full grow">
      {chatHistory.map((chat, index) => {
        if (chat.user === "user")
          return <UserChat chat={chat} key={`chat-${index}`} />;
        if (chat.user === "mimo")
          return <MimoChat chat={chat} key={`chat-${index}`} />;
      })}
    </div>
  );
};

interface UserChatProps {
  chat: Chat;
}

const UserChat = ({ chat }: UserChatProps) => {
  return (
    <div>
      <p>
        {chat.user}: {chat.message}
      </p>
    </div>
  );
};

interface MimoChatProps {
  chat: Chat;
}

const MimoChat = ({ chat }: MimoChatProps) => {
  return (
    <div>
      <p>
        {chat.user}: {chat.message}
      </p>
    </div>
  );
};

export default ChatHistory;
