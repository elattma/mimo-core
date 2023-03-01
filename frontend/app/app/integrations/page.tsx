import Integrations from "@/components/app/integrations/integrations";
import { fetcherWithSession } from "@/lib/server-only-utils";

const Page = async () => {
  const integrations = await fetcherWithSession(
    `${process.env.BASE_URL}/api/proxy/integration`,
    {
      method: "GET",
    }
  );
  console.log(integrations);

  return (
    <main className="p-theme">
      <Integrations />
    </main>
  );
};

export default Page;
