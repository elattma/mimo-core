import { SettingsSidebar } from "@/components/settings-sidebar";
import { TypographyH1 } from "@/components/ui/typography";
import { settingsConfig } from "@/config/settings.config";

type SettingsLayoutProps = {
  children: React.ReactNode;
};

export default function SettingsLayout({ children }: SettingsLayoutProps) {
  return (
    <div className="container space-y-6">
      <TypographyH1>Settings</TypographyH1>
      <div className="flex flex-col gap-6 sm:flex-row">
        <aside className="w-full sm:w-40">
          <SettingsSidebar items={settingsConfig.sidebar} />
        </aside>
        <main className="w-full">{children}</main>
      </div>
    </div>
  );
}
