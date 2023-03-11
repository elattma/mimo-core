import chalk from "chalk";
import { NextRequest } from "next/server";

export const mock_logRequest = (request: NextRequest) => {
  console.log(
    chalk.cyan(`[MOCK] [${new Date().toLocaleTimeString()}] Received request`)
  );
  console.log(request);
  console.log();
};

export const mock_logResponse = (response: Response) => {
  console.log(
    chalk.cyan(`[MOCK] [${new Date().toLocaleTimeString()}] Received response`)
  );
  console.log(response);
  console.log();
};
