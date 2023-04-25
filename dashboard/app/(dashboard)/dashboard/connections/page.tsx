import { ConnectionsManager } from "@/components/connections-manager";
import { TypographyH1 } from "@/components/ui/typography";

export default function ConnectionsPage() {
  return (
    <div className="flex flex-col gap-8">
      <TypographyH1>Connections</TypographyH1>
      <ConnectionsManager />
    </div>
  );
}
