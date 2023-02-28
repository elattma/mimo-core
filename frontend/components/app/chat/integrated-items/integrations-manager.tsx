"use client";

import {
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from "@/components/ui/navigation/dropdown-menu";
import { ChevronDown, Cog, Globe, Star } from "lucide-react";
import type { Dispatch, SetStateAction } from "react";
import { forwardRef, useRef, useState } from "react";

type SelectionType = "all" | "favorites" | "custom";

const IntegrationsManager = () => {
  const allRef = useRef<HTMLDivElement>(null);
  const favoritesRef = useRef<HTMLDivElement>(null);
  const customRef = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<SelectionType>("all");

  return (
    <fieldset className="space-y-theme-1/2">
      <div
        className="flex space-x-theme-1/4"
        role="radiogroup"
        aria-label="Filter by integration"
        onKeyDown={(event) => {
          if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
            switch (selection) {
              case "all":
                customRef.current?.focus();
                setSelection("custom");
                break;
              case "favorites":
                allRef.current?.focus();
                setSelection("all");
                break;
              case "custom":
                favoritesRef.current?.focus();
                setSelection("favorites");
                break;
            }
          } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            switch (selection) {
              case "all":
                favoritesRef.current?.focus();
                setSelection("favorites");
                break;
              case "favorites":
                customRef.current?.focus();
                setSelection("custom");
                break;
              case "custom":
                allRef.current?.focus();
                setSelection("all");
                break;
            }
          }
        }}
      >
        <All ref={allRef} selection={selection} setSelection={setSelection} />
        <Favorites
          ref={favoritesRef}
          selection={selection}
          setSelection={setSelection}
        />
        <Custom
          ref={customRef}
          selection={selection}
          setSelection={setSelection}
        />
      </div>
    </fieldset>
  );
};

interface RadioProps {
  selection: SelectionType;
  setSelection: Dispatch<SetStateAction<SelectionType>>;
}

const All = forwardRef<HTMLDivElement, RadioProps>(
  ({ selection, setSelection }, forwardedRef) => {
    return (
      <div
        className={[
          "flex items-center space-x-theme-1/8 rounded-theme border px-theme-1/4 py-theme-1/8 text-sm transition-colors hover:cursor-pointer",
          selection === "all"
            ? "border-brand-border bg-brand-bg text-brand-text"
            : "border-neutral-border bg-neutral-bg text-gray-text",
        ].join(" ")}
        ref={forwardedRef}
        role="radio"
        aria-checked={selection === "all"}
        aria-label="all"
        tabIndex={0}
        onClick={() => setSelection("all")}
        onKeyDown={(event) => {
          if (event.key === " ") {
            setSelection("all");
          }
        }}
      >
        <Globe className="h-4 w-4" />
        <p className="select-none">All</p>
      </div>
    );
  }
);

const Favorites = forwardRef<HTMLDivElement, RadioProps>(
  ({ selection, setSelection }, forwardedRef) => {
    return (
      <div
        className={[
          "flex h-fit rounded-theme border text-sm",
          selection === "favorites"
            ? "border-brand-border bg-brand-bg text-brand-text"
            : "border-neutral-border bg-neutral-bg text-neutral-text",
        ].join(" ")}
      >
        <div
          ref={forwardedRef}
          className={[
            "flex cursor-pointer items-center space-x-theme-1/8 rounded-l-theme border-r px-theme-1/4 py-theme-1/8 transition-colors",
            selection === "favorites"
              ? "border-brand-border hover:bg-brand-bg-hover focus:bg-brand-bg-hover active:bg-brand-bg-active"
              : "border-neutral-border hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover active:bg-neutral-bg-active",
          ].join(" ")}
          role="radio"
          aria-checked={selection === "favorites"}
          aria-label="favorites"
          tabIndex={0}
          onClick={() => setSelection("favorites")}
          onKeyDown={(event) => {
            if (event.key === " ") {
              setSelection("favorites");
            }
          }}
        >
          <Star className="h-4 w-4" />
          <p className="select-none">Favorites</p>
        </div>
        <DropdownMenuRoot>
          <DropdownMenuTrigger asChild>
            <div
              className={[
                "flex cursor-pointer items-center justify-center rounded-r-theme px-theme-1/8 transition-colors",
                selection === "favorites"
                  ? "hover:bg-brand-bg-hover focus:bg-brand-bg-hover active:bg-brand-bg-active"
                  : "hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover active:bg-neutral-bg-active",
              ].join(" ")}
              role="button"
              tabIndex={0}
              aria-label="configure favorites filter for integrations"
            >
              <ChevronDown className="h-4 w-4" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuGroup>
              <DropdownMenuItem>Google Drive</DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenuRoot>
      </div>
    );
  }
);

const Custom = forwardRef<HTMLDivElement, RadioProps>(
  ({ selection, setSelection }, forwardedRef) => {
    return (
      <div
        className={[
          "flex h-fit rounded-theme border text-sm",
          selection === "custom"
            ? "border-brand-border bg-brand-bg text-brand-text"
            : "border-neutral-border bg-neutral-bg text-neutral-text",
        ].join(" ")}
      >
        <div
          ref={forwardedRef}
          className={[
            "flex cursor-pointer items-center space-x-theme-1/8 rounded-l-theme border-r px-theme-1/4 py-theme-1/8 transition-colors",
            selection === "custom"
              ? "border-brand-border hover:bg-brand-bg-hover focus:bg-brand-bg-hover active:bg-brand-bg-active"
              : "border-neutral-border hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover active:bg-neutral-bg-active",
          ].join(" ")}
          role="radio"
          aria-checked={selection === "custom"}
          aria-label="custom"
          tabIndex={0}
          onClick={() => setSelection("custom")}
          onKeyDown={(event) => {
            if (event.key === " ") {
              setSelection("custom");
            }
          }}
        >
          <Cog className="h-4 w-4" />
          <p className="select-none">Custom</p>
        </div>
        <DropdownMenuRoot>
          <DropdownMenuTrigger asChild>
            <div
              className={[
                "flex cursor-pointer items-center justify-center rounded-r-theme px-theme-1/8 transition-colors",
                selection === "custom"
                  ? "hover:bg-brand-bg-hover focus:bg-brand-bg-hover active:bg-brand-bg-active"
                  : "hover:bg-neutral-bg-hover focus:bg-neutral-bg-hover active:bg-neutral-bg-active",
              ].join(" ")}
              role="button"
              tabIndex={0}
              aria-label="configure custom filter for integrations"
            >
              <ChevronDown className="h-4 w-4" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuGroup>
              <DropdownMenuItem>Google Drive</DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenuRoot>
      </div>
    );
  }
);

export default IntegrationsManager;
