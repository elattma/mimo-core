import { Chat } from "@/models";

type UserChatItemProps = {
  chat: Chat;
};

export default function UserChatItem({ chat }: UserChatItemProps) {
  return (
    // Container to align the chat bubble to the right
    <div className="w-fit min-w-0 max-w-full grow-0 self-end">
      {/* The actual chat bubble; enforces margin when width is full */}
      <div className="ml-theme-2 break-words rounded-t-theme rounded-bl-theme border border-brand-5 bg-brand-bg p-theme-1/2">
        <p className="text-sm text-brand-text-contrast">{chat.message}</p>
      </div>
    </div>
  );
}
