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

export type Integration = {
  name: string;
  id: string;
  category: string;
  categoryName: string;
  icon: string;
};
