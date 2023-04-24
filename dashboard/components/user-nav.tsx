"use client";

import Link from "next/link";
import { LogOut, Settings, Terminal } from "lucide-react";
import { useUser } from "@auth0/nextjs-auth0/client";
import { DropdownMenuItem as DropdownMenuItemPrimitive } from "@radix-ui/react-dropdown-menu";

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
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

function getInitialFromName(name: string): string {
  if (!name) {
    return "";
  } else {
    return name.charAt(0).toLocaleUpperCase();
  }
}

export function UserNav() {
  const user = useUser();
  const [developerMode, setDeveloperMode] = useState<boolean>(false);
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
      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel>My Account</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <Link href="/dashboard/settings/general">
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </Link>
          </DropdownMenuItem>
          <div className="flex items-center justify-between px-2 py-1.5">
            <div className="flex items-center">
              <Terminal className="mr-2 h-4 w-4" />
              <Label className="font-normal" htmlFor="developer-mode">
                Developer Mode
              </Label>
            </div>
            <DropdownMenuItemPrimitive asChild>
              <Switch
                className="data-[state=checked]:bg-teal-500"
                id="developer-mode"
                size="sm"
                defaultChecked
                disabled
              />
            </DropdownMenuItemPrimitive>
          </div>
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
