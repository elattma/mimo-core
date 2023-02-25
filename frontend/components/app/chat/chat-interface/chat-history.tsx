"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { useUser } from "@auth0/nextjs-auth0/client";

const ChatHistory = () => {
  const { chatHistory } = useChatHistoryContext();
  const user = useUser();
  return (
    <div className="w-full grow overflow-auto">
      {chatHistory.map((chat, index) => {
        if (chat.user === "user")
          return (
            <UserChat
              message={chat.message}
              username={user.user?.nickname || user.user?.name || ""}
              key={`chat-${index}`}
            />
          );
        if (chat.user === "mimo")
          return <MimoChat message={chat.message} key={`chat-${index}`} />;
      })}
    </div>
  );
};

interface UserChatProps {
  username: string;
  message: string;
}

const UserChat = ({ username, message }: UserChatProps) => {
  return (
    <div className="w-full p-6">
      <p className="text-neutral-text-contrast">
        {username}: {message}
      </p>
    </div>
  );
};

interface MimoChatProps {
  message: string;
}

const MimoChat = ({ message }: MimoChatProps) => {
  return (
    <div className="w-full border-y border-solid border-neutral-border bg-neutral-bg p-6">
      <p className="text-gray-text-contrast">mimo: {message}</p>
    </div>
  );
};

export default ChatHistory;
