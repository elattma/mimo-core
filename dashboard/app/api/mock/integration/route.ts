import { NextResponse } from "next/server";

const INTEGRATIONS = [
  {
    name: "Google Docs",
    id: "google_docs",
    category: "documents",
    categoryName: "Documents",
    icon: "https://assets.mimo.team/icons/google_docs.svg",
  },
  {
    name: "Gmail",
    id: "google_mail",
    category: "email",
    categoryName: "Email",
    icon: "https://assets.mimo.team/icons/google_mail.svg",
  },
  {
    name: "Zoho CRM",
    id: "zoho_crm",
    category: "crm",
    categoryName: "CRM",
    icon: "https://assets.mimo.team/icons/zoho_crm.svg",
  },
  {
    name: "Zendesk Support",
    id: "zendesk_support",
    category: "customer_support",
    categoryName: "Customer Support",
    icon: "https://assets.mimo.team/icons/zendesk_support.svg",
  },
];

export async function GET() {
  return NextResponse.json({ integrations: INTEGRATIONS });
}
