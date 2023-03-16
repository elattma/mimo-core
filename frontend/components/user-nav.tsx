"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import DefaultProfilePicture from "@/public/images/default-profile-picture.png";
import { useUser } from "@auth0/nextjs-auth0/client";
import Image from "next/image";
import Link from "next/link";

export default function UserNav() {
  const user = useUser();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger>
        <Image
          className="rounded-theme"
          src={user.user?.picture || DefaultProfilePicture}
          width={32}
          height={32}
          alt="Profile picture"
        />
      </DropdownMenuTrigger>
      <DropdownMenuContent loop>
        <DropdownMenuLabel asChild>
          <span className="flex items-center">
            <Image
              className="mr-theme-1/4 rounded-theme"
              src={user.user?.picture || DefaultProfilePicture}
              width={20}
              height={20}
              alt="Profile picture"
            />
            <p>{user.user?.name}</p>
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <Link className="hover:cursor-default" href="/app/settings">
              Settings
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link className="hover:cursor-default" href="/app/settings">
              Profile
            </Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem asChild>
            <a className="hover:cursor-default" href="/api/auth/logout">
              Log out
            </a>
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
