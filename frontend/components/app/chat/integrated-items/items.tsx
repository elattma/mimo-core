fetcherWithSession;
import { fetcherWithSession } from "@/lib/server-only-utils";
import { Item as ItemType } from "@/types/mock";
import Link from "next/link";
import Item from "./item";

const Items = async () => {
  const items = (await fetcherWithSession(
    "http://localhost:3000/api/mock/item",
    {
      method: "GET",
    }
  )) as ItemType[];

  if (items.length < 1) {
    return (
      <div className="w-full space-y-theme-1/2">
        <p className="text-sm font-medium text-gray-text-contrast">Items</p>
        <div className="flex items-center justify-center rounded-theme border border-dashed border-neutral-border">
          <Link
            className="flex justify-center p-theme text-center text-gray-text"
            href="#"
          >
            Lorem ipsum dolor sit, amet consectetur adipisicing elit. Qui,
            necessitatibus.
          </Link>
        </div>
      </div>
    );
  } else {
    return (
      <fieldset className="space-y-theme-1/2">
        {items.map((item, index) => (
          <Item item={item} key={`item-${index}`} />
        ))}
      </fieldset>
    );
  }
};

export default Items;
