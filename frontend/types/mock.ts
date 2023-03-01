export interface Item {
  source: string;
  type: string;
  title: string;
  preview: string;
}

export interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  oauth2_link: string;
  authorized: boolean;
}
