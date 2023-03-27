import IntegratedItems from "@/components/integrated-items";
import UploadedItems from "@/components/uploaded-items";
import { ItemsProvider } from "@/contexts/items-context";
import { serverGet } from "@/lib/server-fetchers";

const Page = async () => {
  const initialData = await serverGet("/item");

  return (
    <>
      <ItemsProvider initialData={initialData}>
        <div className="shrink-1 basis-1/2 pr-theme-1/2 md:pr-0 md:pb-theme-1/2">
          <UploadedItems />
        </div>
        <div className="shrink-1 basis-1/2 pl-theme-1/2 md:pl-0 md:pt-theme-1/2">
          <IntegratedItems />
        </div>
      </ItemsProvider>
    </>
  );
};

export default Page;
