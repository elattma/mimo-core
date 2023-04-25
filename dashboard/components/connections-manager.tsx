"use client";

import { TypographyMuted } from "@/components/ui/typography";
import Image from "next/image";

type ConnectionsManagerProps = {
  connections: any[];
};

export function ConnectionsManager({ connections }: ConnectionsManagerProps) {
  return (
    <div className="flex flex-wrap gap-4">
      {connections.length > 0 ? (
        connections.map((connection, index) => (
          <Connection
            connection={connection}
            key={`TEMP_CONNECTION-${index}`}
          />
        ))
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
  connection: any;
};

function Connection({ connection }: ConnectionProps) {
  return (
    <div className="flex h-36 w-40 flex-col items-center justify-center rounded-sm border bg-neutral-3 p-4">
      <Image
        className="h-6 w-auto"
        src={connection.integration.icon}
        alt={`${connection.integration.name} logo`}
        width={40}
        height={40}
      />
      <p className="text-sm">{connection.name}</p>
    </div>
  );
}
