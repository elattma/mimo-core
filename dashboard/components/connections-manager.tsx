import { TypographyMuted } from "@/components/ui/typography";
import Image from "next/image";
import type { Connection, Integration } from "@/types";
import Link from "next/link";

type ConnectionsManagerProps = {
  connections: Connection[];
  integrations: Integration[];
};

export function ConnectionsManager({
  connections,
  integrations,
}: ConnectionsManagerProps) {
  return (
    <div className="flex flex-wrap gap-4">
      {connections.length > 0 ? (
        connections.map((connection, index) => {
          const integration = integrations.find(
            (integration) => integration.id === connection.integration
          );
          if (integration === undefined) return null;
          return (
            <Connection
              connection={connection}
              integration={integration}
              key={`TEMP_CONNECTION-${index}`}
            />
          );
        })
      ) : (
        <div className="flex h-36 w-40 items-center justify-center rounded-sm border border-dashed p-4">
          <TypographyMuted className="text-center">
            No connections added yet
          </TypographyMuted>
        </div>
      )}
    </div>
  );
}
type ConnectionProps = {
  connection: Connection;
  integration: Integration;
};

function Connection({ connection, integration }: ConnectionProps) {
  return (
    <Link
      className="flex h-36 w-40 flex-col items-center justify-center gap-2 rounded-sm border bg-neutral-3 p-4"
      href={`/dashboard/connections/${connection.id}`}
    >
      <Image
        className="h-6 w-auto"
        src={integration.icon}
        alt={`${integration.name} logo`}
        width={40}
        height={40}
      />
      <p className="font-medium text-neutral-12">{connection.name}</p>
    </Link>
  );
}
