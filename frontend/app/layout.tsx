import type { ReactNode } from "react";
import "./globals.css";

interface Props {
  children: ReactNode;
}

const RootLayout = ({ children }: Props) => {
  return (
    <html className="h-full w-full" lang="en">
      <head />
      <body className="h-full w-full">{children}</body>
    </html>
  );
};

export default RootLayout;
