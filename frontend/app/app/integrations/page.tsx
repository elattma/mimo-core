import Integrations from "@/components/app/integrations/integrations";
import { serverGet } from "@/lib/server-fetchers";

const Page = async () => {
  const integrationData = await serverGet("/integration");

  return (
    <main className="container flex flex-col space-y-theme p-theme">
      <h1 className="text-lg font-medium text-gray-text-contrast">
        Integrations
      </h1>
      <Integrations integrationData={integrationData} />
    </main>
  );
};

export default Page;
