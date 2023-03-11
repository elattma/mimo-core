import TailwindIndicator from "@/components/tailwind-indicator";
import { Toaster } from "@/components/ui/toaster";
import { cn } from "@/lib/util";
import { UserProvider } from "@auth0/nextjs-auth0/client";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";

export const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

type RootLayoutProps = {
  children: ReactNode;
};

const RootLayout = ({ children }: RootLayoutProps) => {
  return (
    <UserProvider>
      <html
        className={cn(
          "bg-neutral-base font-sans text-gray-text antialiased",
          inter.variable
        )}
        lang="en"
      >
        <head />
        <body className="flex min-h-screen flex-col">
          {children}
          <TailwindIndicator />
          <Toaster />
        </body>
      </html>
    </UserProvider>
  );
};

export default RootLayout;
