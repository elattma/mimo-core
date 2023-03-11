/**
 * Inspired by taxonomy by shadcn
 * https://github.com/shadcn/taxonomy
 */

export default function TailwindIndicator() {
  if (process.env.NODE_ENV !== "development") return null;

  return (
    <div className="fixed bottom-1 left-1 z-50 flex h-8 w-8 items-center justify-center rounded-theme bg-neutral-bg font-mono text-xs text-neutral-text-contrast">
      <div className="block sm:hidden">xs</div>
      <div className="hidden sm:block md:hidden lg:hidden xl:hidden 2xl:hidden">
        sm
      </div>
      <div className="hidden md:block lg:hidden xl:hidden 2xl:hidden">md</div>
      <div className="hidden lg:block xl:hidden 2xl:hidden">lg</div>
      <div className="hidden xl:block 2xl:hidden">xl</div>
      <div className="hidden 2xl:block">2xl</div>
    </div>
  );
}
