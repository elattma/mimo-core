import type { Integration } from "@/types/mock";

interface Props {
  integrations: Integration[];
}

const Integrations = ({ integrations }: Props) => {
  return (
    <div>
      {integrations.map((integration, index) => {
        const state = Buffer.from(
          JSON.stringify({
            integrationId: integration.id,
          })
        ).toString("base64");
        const href = `${integration.oauth2_link}&redirect_uri=${process.env.NEXT_PUBLIC_BASE_URL}/auth&state=${state}`;
        return (
          <div key={`integration-${index}`}>
            <p>{integration.name}</p>
            <p>{integration.description}</p>
            <a href={href}>Click to connect</a>
          </div>
        );
      })}
    </div>
  );
};

export default Integrations;
