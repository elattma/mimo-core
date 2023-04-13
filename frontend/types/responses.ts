export type GetEndpoints = {
  "/chat": GetChatResponse;
  "/integration": GetIntegrationResponse;
  "/item": GetItemResponse;
};

export type GetChatResponse = {
  id: string;
  message: string;
  author: string;
  role: string;
  timestamp: number;
}[];

export type GetIntegrationResponse = {
  id: string;
  name: string;
  description: string;
  icon: string;
  oauth2_link: string;
  authorized: boolean;
}[];

export type GetItemResponse = {
  items: {
    integration: string;
    id: string;
    title: string;
    icon: string;
    link: string;
  }[];
  next_token: string;
};

export type PostEndpoints = {
  "/chat": PostChatResponse;
  "/integration": PostIntegrationResponse;
  "/item": PostItemResponse;
};

export type PostChatResponse = {
  id: string;
  message: string;
  author: string;
  role: string;
  timestamp: number;
};

export type PostIntegrationResponse = {};

export type PostItemResponse = {
  signedUrl: string;
};
