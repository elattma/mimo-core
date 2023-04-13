"use client";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useIntegrationsContext } from "@/contexts/integrations-context";
import { useItemsContext } from "@/contexts/items-context";
import { useSelectedItemContext } from "@/contexts/selected-item-context";
import { Integration, Item } from "@/models";
import { DropdownMenuPortal } from "@radix-ui/react-dropdown-menu";
import { cva } from "class-variance-authority";
import { ChevronDown, Cog, Globe, Search as SearchIcon } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import {
  Dispatch,
  SetStateAction,
  forwardRef,
  useCallback,
  useRef,
  useState,
} from "react";

export default function IntegratedItems() {
  const [searchTerm, setSearchTerm] = useState("");

  return (
    <div className="flex h-full w-full min-w-full flex-col space-y-theme-1/2">
      <p className="text-sm font-semibold text-gray-text-contrast">
        Integrated Items
      </p>
      <Filters />
      <Search searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
      <Items />
    </div>
  );
}

type SelectionType = "all" | "custom";

function Filters() {
  const { integrations } = useIntegrationsContext();
  const allRef = useRef<HTMLDivElement>(null);
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
              case "custom":
                allRef.current?.focus();
                setSelection("all");
                break;
            }
          } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
            switch (selection) {
              case "all":
                allRef.current?.focus();
                setSelection("all");
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
        <Custom
          ref={customRef}
          selection={selection}
          setSelection={setSelection}
          integrations={integrations}
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
All.displayName = "All";

const Custom = forwardRef<
  HTMLDivElement,
  RadioProps & { integrations: Integration[] }
>(({ selection, setSelection, integrations }, forwardedRef) => {
  const [selectedIntegrations, setSelectedIntegrations] = useState<
    Record<string, boolean>
  >(
    integrations.reduce((o: Record<string, boolean>, integration) => {
      o[integration.id] = false;
      return o;
    }, {})
  );
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
        <DropdownMenuPortal>
          <DropdownMenuContent align="start">
            <DropdownMenuGroup>
              {integrations.map((integration, index) => (
                <DropdownMenuCheckboxItem
                  key={index}
                  checked={selectedIntegrations[integration.id]}
                  onCheckedChange={(checked) => {
                    setSelectedIntegrations({
                      ...selectedIntegrations,
                      [integration.id]: checked,
                    });
                  }}
                >
                  {integration.name}
                </DropdownMenuCheckboxItem>
              ))}
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            <DropdownMenuGroup>
              <Button className="w-full" variant="ghost" size="sm">
                Apply
              </Button>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenuPortal>
      </DropdownMenu>
    </div>
  );
});
Custom.displayName = "Custom";

type SearchProps = {
  searchTerm: string;
  setSearchTerm: Dispatch<SetStateAction<string>>;
};

function Search({ searchTerm, setSearchTerm }: SearchProps) {
  return (
    <div className="group flex items-center space-x-theme-1/4 rounded-theme border border-neutral-border p-theme-1/8 ring-0 ring-neutral-line transition-[box-shadow] focus-within:ring-2 focus-within:ring-brand-line">
      <SearchIcon className="h-4 w-4 text-gray-text group-focus-within:text-gray-text-contrast" />
      <input
        className="prevent-default-focus flex-1 bg-transparent text-sm text-gray-text-contrast placeholder-gray-text"
        type="text"
        placeholder="Search"
        aria-label="Search integrated items"
        value={searchTerm}
        onChange={(event) => setSearchTerm(event.target.value)}
      />
    </div>
  );
}

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
  const { integratedItems } = useItemsContext();
  const { setSelectedItem } = useSelectedItemContext();
  const [selected, setSelected] = useState<number | null>(null);

  const selectOrUnselectItem = useCallback(
    (item: Item, index: number) => {
      if (selected === index) {
        setSelected(null);
        setSelectedItem(null);
      } else {
        setSelected(index);
        setSelectedItem(item);
      }
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
      <ScrollArea
        className="rounded-theme border border-neutral-border bg-neutral-bg-subtle"
        innerClassName="max-h-52"
      >
        <div className="flex flex-col divide-y divide-neutral-border">
          {integratedItems.map((item, index) => (
            <div
              className={itemVariants({ selected: selected === index })}
              role="checkbox"
              tabIndex={0}
              aria-checked={selected === index}
              aria-label={item.title}
              key={index}
              onClick={(event) => {
                selectOrUnselectItem(item, index);
                event.currentTarget.blur();
              }}
              onKeyDown={(event) => {
                if (event.key === " " || event.key === "Enter")
                  selectOrUnselectItem(item, index);
              }}
            >
              <Image
                draggable={false}
                src={`https://${item.icon}`}
                alt="Item icon"
                width={20}
                height={20}
              />
              <p className="truncate whitespace-nowrap text-sm font-medium">
                {item.title}
              </p>
            </div>
          ))}
        </div>
      </ScrollArea>
    );
  }
}
