import { createAuthLink } from "aws-appsync-auth-link";
import { createSubscriptionHandshakeLink } from "aws-appsync-subscription-link";

import {
  ApolloClient,
  ApolloLink,
  HttpLink,
  InMemoryCache,
} from "@apollo/client";

let client: ApolloClient<any> | null = null;

export const getSubscribeClient = (accessToken: string) => {
  // create a new client if there's no existing one
  // or if we are running on the server.
  if (!client || typeof window === "undefined") {
    const url = process.env.NEXT_PUBLIC_APPSYNC_GRAPHQL_ENDPOINT || "";
    console.log(url);
    const region = "us-east-1";
    const auth = {
      type: "OPENID_CONNECT",
      jwtToken: async () => accessToken,
    };
    console.log(auth);

    const httpLink = new HttpLink({ uri: url });

    const link = ApolloLink.from([
      // @ts-ignore
      createAuthLink({ url, region, auth }),
      // @ts-ignore
      createSubscriptionHandshakeLink({ url, region, auth }, httpLink),
    ]);

    client = new ApolloClient({
      link,
      cache: new InMemoryCache(),
    });
  }

  return client;
};
