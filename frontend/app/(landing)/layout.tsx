// @ts-nocheck

import { cn } from "@/lib/util";
import { ArrowRight } from "lucide-react";
import { Lily_Script_One } from "next/font/google";
import Link from "next/link";
import { ReactNode } from "react";

const logoFont = Lily_Script_One({ weight: "400", subsets: ["latin"] });

type LandingLayoutProps = {
  children: ReactNode;
};

export default function LandingLayout({ children }: LandingLayoutProps) {
  return (
    <div className="flex max-h-screen min-h-0 grow flex-col overflow-y-hidden">
      <header className="container sticky top-0 z-40 pt-theme">
        <div className="flex items-center justify-between rounded-xl border border-neutralA-3 bg-neutral-bg-subtle px-theme py-theme-1/2 shadow-sm">
          <Link
            className={cn(
              "select-none rounded-theme text-2xl leading-none text-brand-solid",
              logoFont.className
            )}
            href="/"
          >
            mimo
          </Link>
          {/* @ts-ignore */}
          <a
            className="flex items-center gap-theme-1/8 rounded-theme text-gray-text-contrast transition-colors hover:text-brand-text focus:text-brand-text"
            href="/api/auth/login"
          >
            <p className="text-sm font-semibold">Log in</p>{" "}
            <ArrowRight width={12} height={12} />
          </a>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}
