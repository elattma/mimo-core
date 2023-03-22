"use client";

import { Integration } from "@/models";
import { GetIntegrationResponse } from "@/types/responses";
import { useEffect, useState } from "react";
import IntegrationFilters from "./integration-filters";
import IntegrationPanel from "./integration-panel";

type Props = {
  integrationData: GetIntegrationResponse;
};

const Integrations = ({ integrationData }: Props) => {
  const allIntegrations = integrationData.map((integration) => {
    return Integration.fromJSON(integration);
  });
  const [integrations, setIntegrations] =
    useState<Integration[]>(allIntegrations);
  const [filterUnauthorized, setFilterUnauthorized] = useState<boolean>(true);
  const [filterAuthorized, setFilterAuthorized] = useState<boolean>(true);

  useEffect(() => {
    if (filterUnauthorized && filterAuthorized) {
      setIntegrations(allIntegrations);
    } else if (filterUnauthorized) {
      setIntegrations(
        allIntegrations.filter((integration) => !integration.authorized)
      );
    } else if (filterAuthorized) {
      setIntegrations(
        allIntegrations.filter((integration) => integration.authorized)
      );
    } else {
      setIntegrations([]);
    }
  }, [filterUnauthorized, filterAuthorized, allIntegrations]);

  return (
    <div className="flex space-x-theme">
      <IntegrationFilters
        setFilterUnauthorized={setFilterUnauthorized}
        setFilterAuthorized={setFilterAuthorized}
      />
      <div className="flex grow gap-theme">
        {integrations.map((integration, index) => (
          <IntegrationPanel
            integration={integration}
            key={`integration-${index}`}
          />
        ))}
      </div>
    </div>
  );
};

export default Integrations;
