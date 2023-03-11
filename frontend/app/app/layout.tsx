import MainNav from "@/components/main-nav";
import UserNav from "@/components/user-nav";
import { appConfig } from "@/config/app";
import type { ReactNode } from "react";

type AppLayoutProps = {
  children?: ReactNode;
};

const AppLayout = async ({ children }: AppLayoutProps) => {
  return (
    <div className="flex max-h-screen min-h-0 grow flex-col space-y-theme overflow-y-hidden">
      <header className="top container sticky z-40 bg-neutral-base">
        <div className="flex items-center justify-between border-b border-b-neutral-border py-theme-1/2">
          <MainNav items={appConfig.mainNav} />
          <UserNav />
        </div>
      </header>
      {children}
    </div>
  );
};

export default AppLayout;
