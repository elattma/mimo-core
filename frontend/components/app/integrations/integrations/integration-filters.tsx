"use client";

import { Switch, SwitchThumb } from "@/components/ui/switch";
import { Dispatch, SetStateAction } from "react";

type Props = {
  setFilterUnauthorized: Dispatch<SetStateAction<boolean>>;
  setFilterAuthorized: Dispatch<SetStateAction<boolean>>;
};

const IntegrationFilters = ({
  setFilterUnauthorized,
  setFilterAuthorized,
}: Props) => {
  return (
    <div className="flex h-fit shrink-0 flex-col space-y-theme-1/2 rounded bg-neutral-bg p-theme-1/2">
      <h2 className="text-sm font-medium text-neutral-text-contrast">
        Filters
      </h2>
      <div className="flex items-center justify-between">
        <label
          className="mr-theme-1/2 text-sm text-neutral-text-contrast"
          htmlFor="unauthorized"
        >
          Unauthorized
        </label>
        <Switch
          name="unauthorized"
          onCheckedChange={setFilterUnauthorized}
          defaultChecked
        >
          <SwitchThumb />
        </Switch>
      </div>
      <div className="flex items-center justify-between">
        <label
          className="mr-theme-1/2 text-sm text-neutral-text-contrast"
          htmlFor="authorized"
        >
          Authorized
        </label>
        <Switch
          name="authorized"
          onCheckedChange={setFilterAuthorized}
          defaultChecked
        >
          <SwitchThumb />
        </Switch>
      </div>
    </div>
  );
};

export default IntegrationFilters;
