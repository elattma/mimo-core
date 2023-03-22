import { Chat } from "@/models";

type UserChatItemProps = {
  chat: Chat;
};

export default function UserChatItem({ chat }: UserChatItemProps) {
  return (
    <div className="w-fit min-w-0 max-w-full grow-0 self-end">
      <div className="ml-theme-2 rounded-t-theme rounded-bl-theme border border-brand-5 bg-brand-bg p-theme-1/2">
        <p className="whitespace-pre-wrap break-words text-sm text-brand-text-contrast">
          {chat.message}
        </p>
      </div>
    </div>
  );
}
