import MainNav from "@/components/main-nav";
import UserNav from "@/components/user-nav";
import { appConfig } from "@/config/app";
import { IntegrationsProvider } from "@/contexts/integrations-context";
import { serverGet } from "@/lib/server-fetchers";
import type { ReactNode } from "react";

type AppLayoutProps = {
  children?: ReactNode;
};

const AppLayout = async ({ children }: AppLayoutProps) => {
  const integrationsData = await serverGet("/integration");

  return (
    <div className="flex max-h-screen min-h-0 grow flex-col overflow-y-hidden">
      <header className="container sticky top-0 z-40 bg-neutral-base">
        <div className="flex items-center justify-between border-b border-b-neutral-border py-theme-1/2">
          <MainNav items={appConfig.mainNav} />
          <UserNav />
        </div>
      </header>
      <IntegrationsProvider initial={integrationsData}>
        {children}
      </IntegrationsProvider>
    </div>
  );
};

export default AppLayout;
