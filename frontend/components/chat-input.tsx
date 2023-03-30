"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { useChatHistoryContext } from "@/contexts/chat-history-context";
import { clientPost } from "@/lib/client-fetchers";
import { Chat } from "@/models";
import { useUser } from "@auth0/nextjs-auth0/client";
import { Send } from "lucide-react";
import { FormEventHandler, useRef, useState } from "react";
import TextareaAutosize from "react-textarea-autosize";

export default function ChatInput() {
  const user = useUser();
  const { addToChatHistory } = useChatHistoryContext();
  const sendButtonRef = useRef<HTMLButtonElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [message, setMessage] = useState("");
  const [dataEnabled, setDataEnabled] = useState<boolean>(false);

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const trimmedMessage = message.trim();
    if (trimmedMessage === "") return;
    if (!user.user?.sub) throw new Error("User is not logged in");
    const chat = new Chat(trimmedMessage, user?.user?.sub);
    addToChatHistory(chat);
    clientPost("/chat", { body: JSON.stringify({ chat: chat.toJSON() }) }).then(
      (response) => {
        const assistantChat = new Chat(
          response.message,
          response.author,
          response.id,
          response.timestamp,
          Chat.Role.ASSISTANT
        );
        addToChatHistory(assistantChat);
      }
    );
    setMessage("");
  };

  return (
    <form
      className="group flex h-fit w-full flex-col divide-y divide-neutralA-3 rounded-theme border border-neutralA-3 bg-neutral-base shadow-2xl transition-[box-shadow] focus-within:ring-2 focus-within:ring-brand-line lg:w-[600px] xl:w-[800px]"
      onSubmit={handleSubmit}
      autoComplete="off"
    >
      <div className="flex w-full items-center gap-theme-1/4 py-theme-1/4 px-theme-1/2">
        <Checkbox
          size="sm"
          checked={dataEnabled}
          onCheckedChange={(checked) => {
            if (typeof checked === "boolean") setDataEnabled(checked);
            else setDataEnabled(false);
          }}
        />
        <label className="text-sm text-neutral-text" htmlFor="data">
          Enable data
        </label>
      </div>
      <div className="flex h-fit w-full items-end gap-theme-1/2 p-theme-1/2">
        <TextareaAutosize
          ref={textareaRef}
          className="scrollbar-track-hidden prevent-default-focus grow resize-none bg-transparent text-gray-text-contrast outline-none placeholder:text-gray-10"
          minRows={1}
          maxRows={5}
          placeholder="Ask me anything..."
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              sendButtonRef.current?.click();
            }
          }}
        />
        <button
          ref={sendButtonRef}
          className="rounded-theme bg-transparent py-theme-1/8 pl-theme-1/4 pr-theme-1/2 transition-colors focus:bg-brand-solid-hover active:bg-brand-11 group-focus-within:bg-brand-solid hover:group-focus-within:bg-brand-solid-hover"
          type="submit"
          onClick={(event) => {
            event.currentTarget.blur();
            textareaRef.current?.focus();
          }}
        >
          <Send
            className="rotate-45 stroke-neutral-text transition-colors group-focus-within:stroke-brand-on-solid"
            width={18}
            height={18}
          />
        </button>
      </div>
    </form>
  );
}
