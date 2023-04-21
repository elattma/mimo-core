export type NavItem = {
  title: string;
  href: string;
  disabled?: boolean;
};

export type SettingsConfig = {
  sidebar: NavItem[];
};
