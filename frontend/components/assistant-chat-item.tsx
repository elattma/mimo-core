import { Chat } from "@/models";

type AssistantChatItemProps = {
  chat: Chat;
};

export default function AssistantChatItem({ chat }: AssistantChatItemProps) {
  return (
    <div className="w-fit min-w-0 max-w-full grow-0 self-start">
      <div className="mr-theme-2 break-words rounded-t-theme rounded-br-theme border border-neutral-5 bg-neutral-bg p-theme-1/2">
        <p className="whitespace-pre-wrap break-words text-sm text-brand-text-contrast">
          {chat.message}
        </p>
      </div>
    </div>
  );
}
