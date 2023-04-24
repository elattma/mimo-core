import { MainNav } from "@/components/main-nav";
import { UserNav } from "@/components/user-nav";
import { dashboardConfig } from "@/config/dashboard.config";

type DashboardLayoutProps = {
  children: React.ReactNode;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="mx-auto flex min-h-screen flex-col space-y-6">
      <header className="container sticky top-0 z-40 bg-background">
        <div className="flex items-center justify-between border-b py-4">
          <MainNav items={dashboardConfig.mainNav} />
          <UserNav />
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </div>
  );
}
