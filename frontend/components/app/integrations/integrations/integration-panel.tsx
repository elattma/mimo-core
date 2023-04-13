import { Integration } from "@/models";
import Image from "next/image";

type Props = {
  integration: Integration;
};

const IntegrationPanel = ({ integration }: Props) => {
  const Comp = integration.authorized ? "a" : "a";
  const compProps = false
    ? {}
    : {
        href: `${integration.oauth2_link}&redirect_uri=${
          process.env.NEXT_PUBLIC_BASE_URL
        }/auth&state=${Buffer.from(
          JSON.stringify({
            integration: integration.id,
          })
        ).toString("base64")}`,
      };

  return (
    <Comp
      className="rounded-theme border border-neutral-border p-theme shadow-none transition-all hover:border-neutral-border-hover hover:shadow focus:border-neutral-border-hover focus:shadow"
      {...compProps}
    >
      <Image
        src={`https://${integration.icon}`}
        alt={`Logo for ${integration.name}`}
        width={20}
        height={20}
      ></Image>
      <p className="font-medium text-neutral-text-contrast">
        {integration.name}
      </p>
      <p className="text-sm text-neutral-text-contrast">
        {integration.description}
      </p>
    </Comp>
  );
};

export default IntegrationPanel;
