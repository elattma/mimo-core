import { ConnectionAdder } from "@/components/connection-adder";
import { ConnectionsManager } from "@/components/connections-manager";
import { TypographyH1 } from "@/components/ui/typography";
import { serverGet } from "@/lib/server-fetchers";

export default async function ConnectionsPage() {
  const getIntegrationResponse = await serverGet("/integration");

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <TypographyH1>Connections</TypographyH1>
        <ConnectionAdder integrations={getIntegrationResponse.integrations} />
      </div>
      <ConnectionsManager connections={[]} />
    </div>
  );
}
