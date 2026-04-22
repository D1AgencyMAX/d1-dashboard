// Thin wrapper around Meta's WhatsApp Business Cloud API (Graph API v21).
// Docs: https://developers.facebook.com/docs/whatsapp/cloud-api

const GRAPH_VERSION = process.env.WHATSAPP_GRAPH_VERSION ?? "v21.0";

function token() {
  const t = process.env.WHATSAPP_ACCESS_TOKEN;
  if (!t) throw new Error("WHATSAPP_ACCESS_TOKEN not set");
  return t;
}

function base(phoneNumberId: string) {
  return `https://graph.facebook.com/${GRAPH_VERSION}/${phoneNumberId}`;
}

type WaSendResult = { wa_message_id: string | null; raw: unknown };

async function post(url: string, body: unknown): Promise<unknown> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`WhatsApp API error ${res.status}: ${JSON.stringify(json)}`);
  }
  return json;
}

export async function sendText(
  phoneNumberId: string,
  to: string,
  text: string,
): Promise<WaSendResult> {
  const json = (await post(`${base(phoneNumberId)}/messages`, {
    messaging_product: "whatsapp",
    recipient_type: "individual",
    to,
    type: "text",
    text: { body: text, preview_url: false },
  })) as { messages?: Array<{ id: string }> };
  return { wa_message_id: json.messages?.[0]?.id ?? null, raw: json };
}

export async function sendAudio(
  phoneNumberId: string,
  to: string,
  mediaId: string,
): Promise<WaSendResult> {
  const json = (await post(`${base(phoneNumberId)}/messages`, {
    messaging_product: "whatsapp",
    recipient_type: "individual",
    to,
    type: "audio",
    audio: { id: mediaId },
  })) as { messages?: Array<{ id: string }> };
  return { wa_message_id: json.messages?.[0]?.id ?? null, raw: json };
}

export async function sendTemplate(
  phoneNumberId: string,
  to: string,
  templateName: string,
  languageCode = "en_US",
  components: unknown[] = [],
): Promise<WaSendResult> {
  const json = (await post(`${base(phoneNumberId)}/messages`, {
    messaging_product: "whatsapp",
    to,
    type: "template",
    template: {
      name: templateName,
      language: { code: languageCode },
      components,
    },
  })) as { messages?: Array<{ id: string }> };
  return { wa_message_id: json.messages?.[0]?.id ?? null, raw: json };
}

export async function markAsRead(phoneNumberId: string, waMessageId: string): Promise<void> {
  await post(`${base(phoneNumberId)}/messages`, {
    messaging_product: "whatsapp",
    status: "read",
    message_id: waMessageId,
  });
}

// Upload a binary blob (OGG audio for voice notes) and return a media ID.
export async function uploadMedia(
  phoneNumberId: string,
  bytes: Uint8Array,
  mimeType: string,
  filename = "voice.ogg",
): Promise<string> {
  const form = new FormData();
  form.append("messaging_product", "whatsapp");
  form.append("type", mimeType);
  form.append("file", new Blob([new Uint8Array(bytes)], { type: mimeType }), filename);

  const res = await fetch(`${base(phoneNumberId)}/media`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token()}` },
    body: form,
  });
  const json = (await res.json().catch(() => ({}))) as { id?: string; error?: unknown };
  if (!res.ok || !json.id) {
    throw new Error(`WhatsApp media upload failed: ${JSON.stringify(json)}`);
  }
  return json.id;
}

// Download inbound media (voice notes, images). Two step: resolve URL, fetch bytes.
export async function downloadMedia(mediaId: string): Promise<{ bytes: Uint8Array; mimeType: string }> {
  const metaRes = await fetch(`https://graph.facebook.com/${GRAPH_VERSION}/${mediaId}`, {
    headers: { Authorization: `Bearer ${token()}` },
  });
  const meta = (await metaRes.json().catch(() => ({}))) as { url?: string; mime_type?: string };
  if (!metaRes.ok || !meta.url) {
    throw new Error(`Could not resolve media ${mediaId}: ${JSON.stringify(meta)}`);
  }
  const binRes = await fetch(meta.url, {
    headers: { Authorization: `Bearer ${token()}` },
  });
  if (!binRes.ok) {
    throw new Error(`Media download failed (${binRes.status})`);
  }
  const arrayBuf = await binRes.arrayBuffer();
  return {
    bytes: new Uint8Array(arrayBuf),
    mimeType: meta.mime_type ?? "application/octet-stream",
  };
}

// Webhook payload shapes, narrowed to what we consume.
export type InboundWebhookMessage = {
  from: string;
  id: string;
  timestamp: string;
  type: "text" | "audio" | "image" | "sticker" | string;
  text?: { body: string };
  audio?: { id: string; mime_type: string; voice?: boolean };
  image?: { id: string; mime_type: string };
  sticker?: { id: string; mime_type: string };
};

export type InboundWebhookContact = {
  wa_id: string;
  profile?: { name?: string };
};

export type InboundWebhookChange = {
  value: {
    messaging_product: "whatsapp";
    metadata: { display_phone_number: string; phone_number_id: string };
    contacts?: InboundWebhookContact[];
    messages?: InboundWebhookMessage[];
    statuses?: Array<{ id: string; status: string; recipient_id: string }>;
  };
  field: "messages";
};

export type InboundWebhookBody = {
  object: "whatsapp_business_account";
  entry: Array<{ id: string; changes: InboundWebhookChange[] }>;
};

// Meta signs every webhook with the App Secret. Reject anything that does not match.
export async function verifySignature(
  rawBody: string,
  signatureHeader: string | null,
): Promise<boolean> {
  const secret = process.env.WHATSAPP_APP_SECRET;
  if (!secret) return false;
  if (!signatureHeader) return false;
  const provided = signatureHeader.replace(/^sha256=/, "");

  const enc = new TextEncoder();
  const keyData = enc.encode(secret);
  const key = await crypto.subtle.importKey(
    "raw",
    keyData,
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(rawBody));
  const expected = Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  if (expected.length !== provided.length) return false;
  let mismatch = 0;
  for (let i = 0; i < expected.length; i++) {
    mismatch |= expected.charCodeAt(i) ^ provided.charCodeAt(i);
  }
  return mismatch === 0;
}
