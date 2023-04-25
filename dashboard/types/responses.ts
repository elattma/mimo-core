import type { Integration } from "@/types";

export type GetEndpoints = {
  "/locksmith": GetLocksmithResponse;
  "/integration": GetIntegrationResponse;
};

export type GetLocksmithResponse = {
  apiKey: {
    value: string;
  };
};

export type GetIntegrationResponse = {
  integrations: Integration[];
};

export type PostEndpoints = {
  "/locksmith": PostLocksmithResponse;
};

export type PostLocksmithResponse = {
  apiKey: {
    value: string;
  };
};
