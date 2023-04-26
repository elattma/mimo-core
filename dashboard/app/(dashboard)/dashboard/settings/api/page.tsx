import { ApiKeyManager } from "@/components/api-key-manager";
import { TypographyH2 } from "@/components/ui/typography";
import { serverGet, serverPost } from "@/lib/server-fetchers";
import type {
  GetLocksmithResponse,
  PostLocksmithResponse,
} from "@/types/responses";

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
    <div className="flex flex-col gap-12">
      <div className="flex flex-col gap-4">
        <TypographyH2 className="w-full border-b pb-2">API Key</TypographyH2>
        <ApiKeyManager startingApiKey={apiKey} />
      </div>
      <div>
        <TypographyH2 className="w-full border-b pb-2">Usage</TypographyH2>
      </div>
    </div>
  );
}
