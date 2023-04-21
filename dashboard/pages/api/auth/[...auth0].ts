import { handleAuth, handleLogin } from "@auth0/nextjs-auth0";

export default handleAuth({
  async login(req, res) {
    try {
      await handleLogin(req, res, {
        returnTo: process.env.AUTH0_REDIRECT_URL,
        authorizationParams: {
          audience: process.env.AUTH0_AUDIENCE,
          scope: process.env.AUTH0_SCOPE,
        },
      });
    } catch (error: any) {
      res.status(error.status || 400).end(error.message);
    }
  },
});
