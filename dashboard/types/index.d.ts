export type NavItem = {
  title: string;
  href: string;
  disabled?: boolean;
};

export type DashboardConfig = {
  mainNav: NavItem[];
};

export type SettingsConfig = {
  sidebar: NavItem[];
};
