import { ThemeToggler } from "@/components/theme-toggler";
import { TypographyH2 } from "@/components/ui/typography";

export default function GeneralSettingsPage() {
  return (
    <div className="flex flex-col gap-12">
      <div className="flex flex-col gap-4">
        <TypographyH2 className="w-full border-b pb-2">Appearance</TypographyH2>
        <ThemeToggler />
      </div>
    </div>
  );
}
