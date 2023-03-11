import { Integration } from "@/models";

type Props = {
  integration: Integration;
};

const IntegrationPanel = ({ integration }: Props) => {
  const Comp = integration.authorized ? "div" : "a";
  const compProps = integration.authorized
    ? {}
    : {
        href: `${integration.oauth2_link}&redirect_uri=${
          process.env.NEXT_PUBLIC_BASE_URL
        }/auth&state=${Buffer.from(
          JSON.stringify({
            integrationId: integration.id,
          })
        ).toString("base64")}`,
      };

  return (
    <Comp
      className="rounded-theme border border-neutral-border p-theme shadow-none transition-all hover:border-neutral-border-hover hover:shadow focus:border-neutral-border-hover focus:shadow"
      {...compProps}
    >
      <svg
        className="mb-theme-1/4 h-10 w-10"
        dangerouslySetInnerHTML={{ __html: integration.icon }}
      />
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
