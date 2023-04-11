import { Lightbulb } from "lucide-react";

type AssistantThoughtProps = {
  thought: string;
};

export default function AssistantThought({ thought }: AssistantThoughtProps) {
  return (
    <div className="flex items-center space-x-theme-1/8 text-sm">
      <Lightbulb className="h-4 w-4" />
      <p>{thought}</p>
    </div>
  );
}
