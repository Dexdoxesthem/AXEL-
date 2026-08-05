import { NextResponse } from "next/server";

const PASSWORD = process.env.AXEL_PASSWORD || "axel123";
const COOKIE = "axel_auth=1; Max-Age=86400; Path=/; HttpOnly; SameSite=Lax";
const CLEAR_COOKIE = "axel_auth=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));

  if (body.logout) {
    return NextResponse.json(
      { ok: true },
      { headers: { "Set-Cookie": CLEAR_COOKIE } }
    );
  }

  if (body.password === PASSWORD) {
    return NextResponse.json(
      { ok: true },
      { headers: { "Set-Cookie": COOKIE } }
    );
  }

  return NextResponse.json(
    { ok: false, error: "invalid password" },
    { status: 401 }
  );
}
