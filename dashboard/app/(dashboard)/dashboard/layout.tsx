import { DashboardNav } from "@/components/dashboard-nav";
import { UserNav } from "@/components/user-nav";

type DashboardLayoutProps = {
  children: React.ReactNode;
};

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="mx-auto flex min-h-screen flex-col space-y-6">
      <header className="container sticky top-0 z-40 bg-background">
        <div className="flex items-center justify-between border-b py-4">
          <DashboardNav />
          <UserNav />
        </div>
      </header>
      <div className="flex-1">{children}</div>
    </div>
  );
}
