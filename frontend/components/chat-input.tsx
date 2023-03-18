"use client";

import { Switch, SwitchThumb } from "@/components/ui/switch";
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
  const [message, setMessage] = useState("");

  const handleSubmit: FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const trimmedMessage = message.trim();
    if (trimmedMessage === "") return;
    if (!user.user?.sub) throw new Error("User is not logged in");
    const chat = new Chat(trimmedMessage, user?.user?.sub);
    addToChatHistory(chat);
    clientPost("/chat", { body: JSON.stringify({ chat: chat.toJSON() }) }).then(
      (data) => addToChatHistory(Chat.fromJSON(data))
    );
    setMessage("");
  };

  return (
    <form
      className="h-fit w-full rounded-theme lg:w-[600px] xl:w-[800px] flex flex-col border border-neutralA-3 bg-neutral-base shadow-2xl focus-within:ring-2 focus-within:ring-brand-line transition-[box-shadow] group divide-y divide-y-neutralA-3"
      onSubmit={handleSubmit}
      autoComplete="off"
    >
      <div className="w-full py-theme-1/4 px-theme-1/2 flex gap-theme-1/4 items-center">
        <Switch>
          <SwitchThumb />
        </Switch>
        <label className="text-neutral-text" htmlFor="data">Enable data</label>
      </div>
      <div className="w-full flex items-end h-fit p-theme-1/2 gap-theme-1/2">
        <TextareaAutosize
          className="scrollbar-track-hidden grow resize-none text-gray-text-contrast outline-none bg-transparent prevent-default-focus"
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
          className="bg-transparent rounded-theme pl-theme-1/4 pr-theme-1/2 py-theme-1/8 hover:bg-brand-solid-hover focus:bg-brand-solid-hover active:bg-brand-11 transition-colors group-focus-within:bg-brand-solid"
          type="submit"
          onClick={event => event.currentTarget.blur()}
        >
          <Send className="rotate-45 group-focus-within:stroke-brand-on-solid stroke-neutral-text transition-colors" width={18} height={18} />
        </button>
      </div>
    </form>
  );
}
