import ChatHistory from "./chat-history";
import ChatInput from "./chat-input";

const ChatInterface = () => {
  return (
    <div className="flex h-full w-full flex-col items-center">
      <ChatHistory />
      <ChatInput />
    </div>
  );
};

export default ChatInterface;
