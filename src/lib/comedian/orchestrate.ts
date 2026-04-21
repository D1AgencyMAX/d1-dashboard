// Stitches together WhatsApp inbound -> brain -> WhatsApp outbound.
// Called from the webhook route.

import { getServerSupabase } from "./supabase-server";
import type { Character, Conversation, Message, WaNumber } from "./types";
import { generateReply, SAFETY_SENTINEL } from "./brain";
import {
  downloadMedia,
  InboundWebhookMessage,
  sendAudio,
  sendText,
  uploadMedia,
} from "./whatsapp";
import { synthesizeSpeech, transcribeAudio } from "./voice";

export async function handleInboundMessage(
  waNumber: WaNumber,
  contactPhone: string,
  contactProfileName: string | null,
  msg: InboundWebhookMessage,
): Promise<void> {
  if (!waNumber.inbound_enabled) return;
  const supa = getServerSupabase();

  // 1. Find or open a conversation for this (number, contact) pair.
  const convo = await ensureConversation(
    waNumber,
    contactPhone,
    contactProfileName,
  );
  const character = await loadCharacter(convo.character_id);

  // 2. Ingest the inbound message. Transcribe audio if needed.
  const ingested = await ingestInbound(convo.id, msg);
  if (!ingested.userSaid) return; // nothing to reply to (e.g., sticker we don't handle)

  // 3. Pull recent history for the model.
  const { data: history } = await supa
    .from("messages")
    .select("*")
    .eq("conversation_id", convo.id)
    .order("created_at", { ascending: true })
    .limit(40);

  const reply = await generateReply(
    character,
    (history ?? []) as Message[],
    ingested.userSaid,
  );

  // 4. Record assistant turn.
  const wantsAudioReply = ingested.inputWasAudio && character.voice_id && character.voice_provider !== "none";
  let replyText = reply.text;

  if (reply.shouldEndCharacter) {
    await supa
      .from("conversations")
      .update({ status: "flagged", closed_at: new Date().toISOString() })
      .eq("id", convo.id);
  }

  if (!replyText) {
    // Model returned only the sentinel or nothing. Still record, don't send.
    await supa.from("messages").insert({
      conversation_id: convo.id,
      direction: "out",
      kind: "system",
      text: reply.shouldEndCharacter ? SAFETY_SENTINEL : "(empty reply)",
      latency_ms: reply.latencyMs,
      input_tokens: reply.inputTokens,
      output_tokens: reply.outputTokens,
      cost_usd: reply.costUsd,
    });
    return;
  }

  try {
    if (wantsAudioReply && character.voice_id) {
      const tts = await synthesizeSpeech(replyText, character.voice_id);
      const mediaId = await uploadMedia(
        waNumber.wa_phone_number_id,
        tts.bytes,
        "audio/ogg",
      );
      const sent = await sendAudio(waNumber.wa_phone_number_id, contactPhone, mediaId);
      const storagePath = await storeAudio(convo.id, tts.bytes);
      await supa.from("messages").insert({
        conversation_id: convo.id,
        direction: "out",
        kind: "audio",
        wa_message_id: sent.wa_message_id,
        text: null,
        transcript: replyText,
        audio_path: storagePath,
        latency_ms: reply.latencyMs,
        input_tokens: reply.inputTokens,
        output_tokens: reply.outputTokens,
        cost_usd: Number((reply.costUsd + tts.costUsd).toFixed(6)),
      });
    } else {
      const sent = await sendText(waNumber.wa_phone_number_id, contactPhone, replyText);
      await supa.from("messages").insert({
        conversation_id: convo.id,
        direction: "out",
        kind: "text",
        wa_message_id: sent.wa_message_id,
        text: replyText,
        latency_ms: reply.latencyMs,
        input_tokens: reply.inputTokens,
        output_tokens: reply.outputTokens,
        cost_usd: reply.costUsd,
      });
    }
    await supa
      .from("conversations")
      .update({ last_message_at: new Date().toISOString() })
      .eq("id", convo.id);
  } catch (err) {
    await supa.from("messages").insert({
      conversation_id: convo.id,
      direction: "out",
      kind: "system",
      text: "(send failed)",
      error: err instanceof Error ? err.message : String(err),
    });
    throw err;
  }
}

async function ensureConversation(
  waNumber: WaNumber,
  contactPhone: string,
  contactProfileName: string | null,
): Promise<Conversation> {
  const supa = getServerSupabase();
  const { data: existing } = await supa
    .from("conversations")
    .select("*")
    .eq("wa_number_id", waNumber.id)
    .eq("contact_phone", contactPhone)
    .eq("status", "open")
    .order("started_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (existing) return existing as Conversation;

  const characterId = waNumber.default_character_id ?? (await pickDefaultCharacterId());
  const { data: inserted, error } = await supa
    .from("conversations")
    .insert({
      wa_number_id: waNumber.id,
      character_id: characterId,
      contact_phone: contactPhone,
      contact_profile_name: contactProfileName,
      direction: "inbound",
      status: "open",
      started_at: new Date().toISOString(),
      last_message_at: new Date().toISOString(),
    })
    .select("*")
    .single();
  if (error || !inserted) {
    throw new Error(`Could not open conversation: ${error?.message ?? "unknown"}`);
  }
  return inserted as Conversation;
}

async function pickDefaultCharacterId(): Promise<string> {
  const supa = getServerSupabase();
  const { data } = await supa
    .from("characters")
    .select("id")
    .eq("is_active", true)
    .order("created_at", { ascending: true })
    .limit(1)
    .maybeSingle();
  if (!data) throw new Error("No active character configured");
  return data.id as string;
}

async function loadCharacter(id: string): Promise<Character> {
  const supa = getServerSupabase();
  const { data, error } = await supa
    .from("characters")
    .select("*")
    .eq("id", id)
    .single();
  if (error || !data) throw new Error(`Character ${id} not found`);
  return data as Character;
}

type Ingested = { userSaid: string; inputWasAudio: boolean };

async function ingestInbound(
  conversationId: string,
  msg: InboundWebhookMessage,
): Promise<Ingested> {
  const supa = getServerSupabase();
  if (msg.type === "text" && msg.text?.body) {
    await supa.from("messages").insert({
      conversation_id: conversationId,
      direction: "in",
      kind: "text",
      wa_message_id: msg.id,
      text: msg.text.body,
    });
    return { userSaid: msg.text.body, inputWasAudio: false };
  }
  if (msg.type === "audio" && msg.audio?.id) {
    const media = await downloadMedia(msg.audio.id);
    const stt = await transcribeAudio(media.bytes, media.mimeType);
    const path = await storeAudio(conversationId, media.bytes);
    await supa.from("messages").insert({
      conversation_id: conversationId,
      direction: "in",
      kind: "audio",
      wa_message_id: msg.id,
      transcript: stt.text,
      audio_path: path,
      audio_duration_seconds: stt.durationSeconds ?? null,
      cost_usd: stt.costUsd,
    });
    return { userSaid: stt.text, inputWasAudio: true };
  }
  // Unsupported. Record and move on.
  await supa.from("messages").insert({
    conversation_id: conversationId,
    direction: "in",
    kind: msg.type === "image" ? "image" : msg.type === "sticker" ? "sticker" : "system",
    wa_message_id: msg.id,
    text: `(unsupported message type: ${msg.type})`,
  });
  return { userSaid: "", inputWasAudio: false };
}

async function storeAudio(conversationId: string, bytes: Uint8Array): Promise<string> {
  const supa = getServerSupabase();
  const path = `${conversationId}/${Date.now()}.ogg`;
  const { error } = await supa.storage
    .from("call-recordings")
    .upload(path, new Uint8Array(bytes), {
      contentType: "audio/ogg",
      upsert: false,
    });
  if (error) throw new Error(`Storage upload failed: ${error.message}`);
  return path;
}
