"use client";

import Link from "next/link";
import { LogOut, Settings } from "lucide-react";
import { useUser } from "@auth0/nextjs-auth0/client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function getInitialFromName(name: string): string {
  if (!name) {
    return "";
  } else {
    return name.charAt(0).toLocaleUpperCase();
  }
}

export function UserNav() {
  const user = useUser();
  const fallbackText = getInitialFromName(user.user?.name ?? "");
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="rounded-full">
          <Avatar className="hover:cursor-pointer">
            <AvatarImage
              src={user.user?.picture ?? undefined}
              alt="Your profile picture"
            />
            <AvatarFallback className="select-none">
              {fallbackText}
            </AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-40" align="end">
        <DropdownMenuLabel>My Account</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <Link href="/dashboard/settings/general">
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>
            <LogOut className="mr-2 h-4 w-4" />
            <a href="/api/auth/logout">Log out</a>
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
