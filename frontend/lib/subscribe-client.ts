import { ApolloClient, InMemoryCache } from "@apollo/client";
import { WebSocketLink } from "@apollo/client/link/ws";
import * as graphqlPrinter from "graphql/language/printer";
import WebSocket from "isomorphic-ws";
import { SubscriptionClient } from "subscriptions-transport-ws";

const createAppSyncGraphQLOperationAdapter = (api_header: any) => ({
  applyMiddleware: async (options: any, next: any) => {
    options.data = JSON.stringify({
      query:
        typeof options.query === "string"
          ? options.query
          : graphqlPrinter.print(options.query),
      variables: options.variables,
    });

    options.extensions = { authorization: api_header };
    delete options.operationName;
    delete options.variables;

    next();
  },
});

const getSubscribeClient = (token: string) => {
  const API_URL = process.env.NEXT_PUBLIC_APPSYNC_GRAPHQL_ENDPOINT || "";
  const WSS_URL = API_URL.replace("https", "wss").replace(
    "appsync-api",
    "appsync-realtime-api"
  );
  // eslint-disable-next-line camelcase
  const HOST = API_URL.replace("https://", "").replace("/graphql", "");
  // const HOST = REALTIME_API_URI.replace('wss://', '').replace('/graphql', '')
  // eslint-disable-next-line camelcase
  const api_header = {
    host: HOST,
    Authorization: `Bearer ${token}`,
  };
  const header_encode = (obj: any) =>
    Buffer.from(JSON.stringify(obj), "utf-8").toString("base64");

  // eslint-disable-next-line camelcase
  const connection_url =
    WSS_URL +
    "?header=" +
    header_encode(api_header) +
    "&payload=" +
    header_encode({});

  const uuid4 = require("uuid").v4;

  // @ts-ignore
  class UUIDOperationIdSubscriptionClient extends SubscriptionClient {
    generateOperationId() {
      return uuid4();
    }

    processReceivedData(receivedData: any) {
      try {
        const parsedMessage = JSON.parse(receivedData);
        if (parsedMessage?.type === "start_ack") return;
      } catch (e) {
        throw new Error(`Message must be JSON-parsable. Got: ${receivedData}`);
      }
      // @ts-ignore
      super.processReceivedData(receivedData);
    }
  }

  const wsLink = new WebSocketLink(
    new UUIDOperationIdSubscriptionClient(
      connection_url,
      {
        // eslint-disable-next-line no-console
        timeout: 5 * 60 * 1000,
        reconnect: true,
        lazy: true,
        connectionCallback: (err) =>
          console.log("connectionCallback", err ? "ERR" : "OK", err || ""),
      },
      WebSocket
    ).use([createAppSyncGraphQLOperationAdapter(api_header)])
  );

  const subscriptionClient = new ApolloClient({
    cache: new InMemoryCache(),
    link: wsLink,
  });

  return subscriptionClient;
}

export default getSubscribeClient;