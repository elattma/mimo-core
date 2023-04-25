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
    } catch {
      res.status(500).json({ message: "Failed to log in." });
    }
  },
});
