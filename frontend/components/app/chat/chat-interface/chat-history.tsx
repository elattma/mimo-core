"use client";

import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { UserContext, useUser } from "@auth0/nextjs-auth0/client";
import Image from "next/image";
import { inter } from "../../../../app/layout";

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
              user={user}
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
  message: string;
  user: UserContext | null;
}

const UserChat = ({ message, user }: UserChatProps) => {
  return (
    <div className="flex w-full items-start space-x-theme-1/2 border-b border-neutral-border p-theme">
      {user?.user?.picture ? (
        <div className="shrink-0">
          <Image
            draggable={false}
            className="rounded-theme"
            src={user?.user?.picture}
            alt="Your profile picture"
            width={28}
            height={28}
          />
        </div>
      ) : (
        <div>no picture</div>
      )}
      <p className={["text-gray-text-contrast", inter.className].join(" ")}>
        {message}
      </p>
    </div>
  );
};

interface MimoChatProps {
  message: string;
}

const MimoChat = ({ message }: MimoChatProps) => {
  return (
    <div className="flex w-full space-x-theme-1/2 border-b border-neutral-border bg-neutral-bg p-theme">
      <div className="h-7 w-7 shrink-0 rounded-theme bg-gradient-to-br from-brand-6 via-brand-8 to-brand-11"></div>
      <pre className="whitespace-pre-wrap">
        <p className={["text-gray-text-contrast", inter.className].join(" ")}>
          {message}
        </p>
      </pre>
    </div>
  );
};

export default ChatHistory;
