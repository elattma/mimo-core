import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

const Layout = ({ children }: Props) => {
  // TODO: Add header
  return <>{children}</>;
};

export default Layout;
