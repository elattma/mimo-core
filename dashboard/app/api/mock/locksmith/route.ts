import { randomUUID } from "crypto";
import { NextResponse } from "next/server";

export async function GET() {
  const key = randomUUID();
  return NextResponse.json({ apiKey: { value: key } });
}

export async function POST() {
  const key = randomUUID();
  return NextResponse.json({ apiKey: { value: key } });
}
