// Streams a stored voice note from Supabase Storage.
// Path can be passed via ?path=<bucket-path> or resolved from a message id.

import { NextRequest, NextResponse } from "next/server";
import { getServerSupabase } from "@/lib/comedian/supabase-server";

export const runtime = "nodejs";

type Ctx = { params: Promise<{ id: string }> };

export async function GET(req: NextRequest, ctx: Ctx) {
  const { id } = await ctx.params;
  const supa = getServerSupabase();

  let storagePath: string | null = req.nextUrl.searchParams.get("path");
  if (!storagePath) {
    const { data } = await supa
      .from("messages")
      .select("audio_path")
      .eq("id", id)
      .maybeSingle();
    storagePath = data?.audio_path ?? null;
  }
  if (!storagePath) return new NextResponse("not found", { status: 404 });

  const { data, error } = await supa.storage
    .from("call-recordings")
    .createSignedUrl(storagePath, 300);
  if (error || !data?.signedUrl) {
    return new NextResponse(`signed url failed: ${error?.message ?? "unknown"}`, { status: 500 });
  }
  return NextResponse.redirect(data.signedUrl);
}
