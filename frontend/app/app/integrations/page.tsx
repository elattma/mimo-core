import Integrations from "@/components/app/integrations/integrations";
import { fetcherWithSession } from "@/lib/server-only-utils";

const Page = async () => {
  const integrations = await fetcherWithSession(
    `${process.env.NEXT_PUBLIC_BASE_URL}/api/${process.env.NEXT_PUBLIC_MOCK_OR_PROXY}/integration`,
    {
      method: "GET",
    }
  );

  return (
    <main className="p-theme">
      <Integrations integrations={integrations} />
    </main>
  );
};

export default Page;
