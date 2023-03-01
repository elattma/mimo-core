"use client";

import {
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/navigation/dropdown-menu";
import DefaultProfilePicture from "@/public/images/default-profile-picture.png";
import { useUser } from "@auth0/nextjs-auth0/client";
import Image from "next/image";
import Link from "next/link";

const Options = () => {
  return (
    <div className="flex items-center space-x-theme-1/2">
      <ProfileDropdown />
    </div>
  );
};

const ProfileDropdown = () => {
  const user = useUser();

  return (
    <DropdownMenuRoot>
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
            <Link href="/app/settings">Settings</Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/app/settings">Profile</Link>
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenuRoot>
  );
};

export default Options;
