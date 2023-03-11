import IntegratedItems from "@/components/integrated-items";
import UploadedItems from "@/components/uploaded-items";
import { IntegratedItemsProvider } from "@/contexts/integrated-items-context";
import { serverGet } from "@/lib/server-fetchers";

const Page = async () => {
  const initialData = await serverGet("/item");
  console.log(initialData);

  return (
    <>
      <div className="shrink-0 basis-1/2 pr-theme-1/2 md:pr-0 md:pb-theme-1/2">
        <UploadedItems items={[]} />
      </div>
      <div className="shrink-0 basis-1/2 pl-theme-1/2 md:pl-0 md:pt-theme-1/2">
        <IntegratedItemsProvider initialData={initialData}>
          <IntegratedItems />
        </IntegratedItemsProvider>
      </div>
    </>
  );
};

export default Page;
