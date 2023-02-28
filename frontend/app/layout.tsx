import { UserProvider } from "@auth0/nextjs-auth0/client";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

export const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

interface Props {
  children: ReactNode;
}

const RootLayout = ({ children }: Props) => {
  return (
    <UserProvider>
      <html
        className={["h-full w-full bg-neutral-base", inter.className].join(" ")}
        lang="en"
      >
        <head />
        <body className="h-full w-full">{children}</body>
      </html>
    </UserProvider>
  );
};

export default RootLayout;
