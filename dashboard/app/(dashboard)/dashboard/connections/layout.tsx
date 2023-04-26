import { ConnectionAdder } from "@/components/connection-adder";
import { ConnectionsManager } from "@/components/connections-manager";
import { TypographyH1 } from "@/components/ui/typography";
import { ConnectionsProvider } from "@/context/connections";
import { IntegrationsProvider } from "@/context/integrations";
import { serverGet } from "@/lib/server-fetchers";
import type { Connection } from "@/types";

type ConnectionsLayoutProps = {
  children: React.ReactNode;
};

export default async function ConnectionsLayout({
  children,
}: ConnectionsLayoutProps) {
  const getIntegrationResponse = await serverGet("/integration");
  const connection: Connection = {
    id: "abc123",
    name: "Personal Email",
    integration: "google_mail",
    created_at: 1682469291000,
    ingested_at: 1682469500000,
  };

  return (
    <IntegrationsProvider integrations={getIntegrationResponse.integrations}>
      <ConnectionsProvider initialConnections={[connection]}>
        <div className="flex flex-col gap-8">
          <div className="flex items-center justify-between">
            <TypographyH1>Connections</TypographyH1>
            <ConnectionAdder
              integrations={getIntegrationResponse.integrations}
            />
          </div>
          <ConnectionsManager
            connections={[connection]}
            integrations={getIntegrationResponse.integrations}
          />
          {children}
        </div>
      </ConnectionsProvider>
    </IntegrationsProvider>
  );
}
