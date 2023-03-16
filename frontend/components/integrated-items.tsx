"use client";

import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useIntegratedItemsContext } from "@/contexts/integrated-items-context";
import { cva } from "class-variance-authority";
import { ChevronDown, Cog, Globe, Star } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  Dispatch,
  SetStateAction,
  forwardRef,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export default function IntegratedItems() {
  return (
    <div className="flex h-full w-full min-w-full flex-col space-y-theme-1/2">
      <p className="text-sm font-semibold text-gray-text-contrast">
        Integrated Items
      </p>
      <Filters />
      <Items />
    </div>
  );
}

type SelectionType = "all" | "favorites" | "custom";

function Filters() {
  const allRef = useRef<HTMLDivElement>(null);
  const favoritesRef = useRef<HTMLDivElement>(null);
  const customRef = useRef<HTMLDivElement>(null);
  const [selection, setSelection] = useState<SelectionType>("all");

  return (
    <fieldset className="max-w-full space-y-theme-1/2">
      <div
        className="flex flex-wrap gap-theme-1/4"
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
}

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
    const [checked, setChecked] = useState<boolean>(false);
    useEffect(() => {
      console.log(checked);
    }, [checked]);
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
        <DropdownMenu>
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
              <DropdownMenuCheckboxItem
                checked={checked}
                onCheckedChange={setChecked}
              >
                Google Drive
              </DropdownMenuCheckboxItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
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
        <DropdownMenu>
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
        </DropdownMenu>
      </div>
    );
  }
);

const itemVariants = cva(
  "flex select-none items-center space-x-theme-1/2 p-theme-1/2 transition-colors hover:cursor-pointer prevent-default-focus outline-none",
  {
    variants: {
      selected: {
        true: "bg-brand-bg text-brand-text-contrast hocus:bg-brand-bg-hover active:bg-brand-bg-active",
        false:
          "text-gray-text hocus:bg-neutral-bg-hover active:bg-neutral-bg-active bg-transparent",
      },
    },
  }
);

function Items() {
  const { integratedItems } = useIntegratedItemsContext();
  const [selected, setSelected] = useState<number | null>(null);

  const selectOrUnselectItem = useCallback(
    (index: number) => {
      console.log(index, selected);
      if (selected === index) setSelected(null);
      else setSelected(index);
    },
    [selected]
  );

  if (integratedItems.length === 0) {
    return (
      <div className="rounded-theme border border-dashed border-neutral-border p-theme">
        <span className="inline-flex text-center text-sm text-gray-text">
          <p>
            You have no integrated items. Navigate to{" "}
            <Link className="text-info-text underline" href="/app/integrations">
              Integrations
            </Link>{" "}
            to add some.
          </p>
        </span>
      </div>
    );
  } else {
    return (
      <ScrollArea className="grow rounded-theme border border-neutral-border bg-neutral-bg-subtle">
        <div className="divide-y-neutral-border flex flex-col divide-y">
          {integratedItems.map((item, index) => (
            <div
              className={itemVariants({ selected: selected === index })}
              role="checkbox"
              tabIndex={0}
              aria-checked={selected === index}
              aria-label={item.title}
              key={index}
              onClick={() => selectOrUnselectItem(index)}
              onKeyDown={(event) => {
                if (event.key === " " || event.key === "Enter")
                  selectOrUnselectItem(index);
              }}
            >
              <Image
                draggable={false}
                src={item.icon}
                alt="Item icon"
                width={20}
                height={20}
              />
              <p className="text-sm font-medium">{item.title}</p>
            </div>
          ))}
        </div>
      </ScrollArea>
    );
  }
}
