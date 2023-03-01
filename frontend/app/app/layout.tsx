import AppHeader from "@/components/app/app-header";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

const Layout = ({ children }: Props) => {
  return (
    <div className="flex h-full flex-col">
      <AppHeader />
      {children}
    </div>
  );
};

export default Layout;
