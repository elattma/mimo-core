"use client";

import DocsLogo from "@/public/icons/docs.svg";
import type { Item as ItemType } from "@/types/mock";
import Image from "next/image";
import { useState } from "react";

interface Props {
  item: ItemType;
}

const Item = ({ item }: Props) => {
  const [checked, setChecked] = useState<boolean>(false);

  return (
    <div
      className={[
        "flex select-none items-center space-x-theme-1/2 rounded-theme border p-theme-1/2 transition-colors hover:cursor-pointer",
        checked
          ? "border-brand-border bg-brand-bg text-brand-text-contrast hover:border-brand-border-hover hover:bg-brand-bg-hover focus:border-brand-border-hover focus:bg-brand-bg-hover active:bg-brand-bg-active"
          : "border-neutral-border text-gray-text hover:border-neutral-border-hover hover:bg-neutral-bg-hover focus:border-neutral-border-hover focus:bg-neutral-bg-hover active:bg-neutral-bg-active",
      ].join(" ")}
      // TODO: Switch to radio
      role="checkbox"
      tabIndex={0}
      aria-checked={checked}
      aria-label={item.title}
      onClick={(event) => {
        setChecked(!checked);
        event.currentTarget.blur();
      }}
      onKeyDown={(event) => {
        if (event.key === " ") {
          setChecked(!checked);
        }
      }}
    >
      <Image
        draggable={false}
        src={DocsLogo}
        alt="Docs logo"
        width={20}
        height={20}
      />
      <p className="text-sm font-medium">{item.title}</p>
    </div>
  );
};

export default Item;
