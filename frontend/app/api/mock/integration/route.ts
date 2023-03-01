import { NextRequest } from "next/server";

const GET = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  const response = new Response(
    JSON.stringify([
      {
        id: "google",
        name: "Google Drive",
        description: "Some description for Google",
        icon:
          "\n" +
          '  <svg viewBox="0 0 87.3 78" xmlns="http://www.w3.org/2000/svg">\n' +
          "    <path\n" +
          '      d="m6.6 66.85 3.85 6.65c.8 1.4 1.95 2.5 3.3 3.3l13.75-23.8h-27.5c0 1.55.4 3.1 1.2 4.5z"\n' +
          '      fill="#0066da"\n' +
          "    />\n" +
          "    <path\n" +
          '      d="m43.65 25-13.75-23.8c-1.35.8-2.5 1.9-3.3 3.3l-25.4 44a9.06 9.06 0 0 0 -1.2 4.5h27.5z"\n' +
          '      fill="#00ac47"\n' +
          "    />\n" +
          "    <path\n" +
          '      d="m73.55 76.8c1.35-.8 2.5-1.9 3.3-3.3l1.6-2.75 7.65-13.25c.8-1.4 1.2-2.95 1.2-4.5h-27.502l5.852 11.5z"\n' +
          '      fill="#ea4335"\n' +
          "    />\n" +
          "    <path\n" +
          '      d="m43.65 25 13.75-23.8c-1.35-.8-2.9-1.2-4.5-1.2h-18.5c-1.6 0-3.15.45-4.5 1.2z"\n' +
          '      fill="#00832d"\n' +
          "    />\n" +
          "    <path\n" +
          '      d="m59.8 53h-32.3l-13.75 23.8c1.35.8 2.9 1.2 4.5 1.2h50.8c1.6 0 3.15-.45 4.5-1.2z"\n' +
          '      fill="#2684fc"\n' +
          "    />\n" +
          "    <path\n" +
          '      d="m73.4 26.5-12.7-22c-.8-1.4-1.95-2.5-3.3-3.3l-13.75 23.8 16.15 28h27.45c0-1.55-.4-3.1-1.2-4.5z"\n' +
          '      fill="#ffba00"\n' +
          "    />\n" +
          "  </svg>\n",
        oauth2_link:
          "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline&prompt=consent",
        authorized: false,
      },
    ]),
    {
      status: 200,
      statusText: "OK",
    }
  );
  return response;
};

const POST = async (request: NextRequest) => {
  if (process.env.NODE_ENV !== "development") {
    return new Response(null, {
      status: 400,
      statusText: "This endpoint is only available in development",
    });
  }
  const response = new Response(JSON.stringify({ message: "OK" }), {
    status: 200,
    statusText: "OK",
  });
  return response;
};

export { GET, POST };
