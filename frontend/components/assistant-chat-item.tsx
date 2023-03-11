import { Chat } from "@/models";

type AssistantChatItemProps = {
  chat: Chat;
};

export default function AssistantChatItem({ chat }: AssistantChatItemProps) {
  return (
    // Container to align the chat bubble to the right
    <div className="w-fit min-w-0 max-w-full grow-0 self-start">
      {/* The actual chat bubble; enforces margin when width is full */}
      <div className="mr-theme-2 break-words rounded-theme border border-neutral-5 bg-neutral-bg p-theme-1/2">
        <p className="text-sm text-neutral-text-contrast">{chat.message}</p>
      </div>
    </div>
  );
}
