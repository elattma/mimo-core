import { ApiKeyManager } from "@/components/api-key-manager";
import { TypographyH2 } from "@/components/ui/typography";
import { serverGet, serverPost } from "@/lib/server-fetchers";
import { GetLocksmithResponse, PostLocksmithResponse } from "@/types/responses";

export default async function ApiSettingsPage() {
  const getLocksmithResponse: GetLocksmithResponse = await serverGet(
    "/locksmith"
  );
  let apiKey = getLocksmithResponse.apiKey.value;
  if (!getLocksmithResponse.apiKey.value) {
    const postLocksmithResponse: PostLocksmithResponse = await serverPost(
      "/locksmith"
    );
    apiKey = postLocksmithResponse.apiKey.value;
  }

  return (
    <div className="flex flex-col space-y-8">
      <div className="flex flex-col space-y-4">
        <TypographyH2 className="w-full border-b pb-2">API Key</TypographyH2>
        <ApiKeyManager startingApiKey={apiKey} />
      </div>
    </div>
  );
}
