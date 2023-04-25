import { MainNav } from "@/components/main-nav";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { TypographyMuted } from "@/components/ui/typography";
import { UserNav } from "@/components/user-nav";
import { dashboardConfig } from "@/config/dashboard.config";
import { DeveloperModeProvider } from "@/context/developer-mode";

type DashboardLayoutProps = {
  children: React.ReactNode;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <DeveloperModeProvider>
      <div className="mx-auto flex min-h-screen flex-col space-y-6">
        <header className="container sticky top-0 z-40 bg-background">
          <div className="flex items-center justify-between border-b border-teal-500 py-4">
            <MainNav items={dashboardConfig.mainNav} />
            <UserNav />
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="mx-auto w-fit rounded-b-sm bg-teal-500 px-1">
                <p className="select-none text-xs font-medium text-white">
                  Developer Mode
                </p>
              </div>
            </TooltipTrigger>
            <TooltipContent className="max-w-xs" side="bottom">
              <TypographyMuted>
                Developer Mode can be toggled under the profile dropdown in the
                top right.
              </TypographyMuted>
            </TooltipContent>
          </Tooltip>
        </header>
        <div className="container flex-1">{children}</div>
      </div>
    </DeveloperModeProvider>
  );
}
