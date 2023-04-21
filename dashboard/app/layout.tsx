import { Metadata } from "next";
import { UserProvider } from "@auth0/nextjs-auth0/client";

import "@/styles/globals.css";
import { TailwindIndicator } from "@/components/tailwind-indicator";
import { ThemeProvider } from "@/components/theme-provider";
import { fontMono, fontSans } from "@/lib/fonts";
import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";

export const metadata: Metadata = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
};

type RootLayoutProps = {
  children: React.ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <UserProvider>
      <TooltipProvider>
        <html
          className={cn(fontSans.variable, fontMono.variable)}
          lang="en"
          suppressHydrationWarning
        >
          <head />
          <body className={"relative min-h-screen font-sans antialiased"}>
            <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
              {children}
              <TailwindIndicator />
            </ThemeProvider>
          </body>
        </html>
      </TooltipProvider>
    </UserProvider>
  );
}
