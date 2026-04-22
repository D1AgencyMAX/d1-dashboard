export type WaNumber = {
  id: string;
  label: string;
  display_number: string;
  wa_phone_number_id: string;
  wa_business_account_id: string;
  default_character_id: string | null;
  inbound_enabled: boolean;
  outbound_enabled: boolean;
  created_at: string;
};

export type Character = {
  id: string;
  slug: string;
  name: string;
  tagline: string | null;
  system_prompt: string;
  style_notes: string | null;
  voice_provider: "elevenlabs" | "openai" | "none";
  voice_id: string | null;
  model: string;
  temperature: number;
  max_output_tokens: number;
  avatar_emoji: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type OutboundRelease = {
  id: string;
  target_phone: string;
  target_name: string | null;
  signer_name: string;
  signer_relationship: string | null;
  signer_signature: string;
  signed_at: string;
  expires_at: string | null;
  notes: string | null;
  revoked_at: string | null;
};

export type Conversation = {
  id: string;
  wa_number_id: string;
  character_id: string;
  release_id: string | null;
  contact_phone: string;
  contact_profile_name: string | null;
  direction: "inbound" | "outbound";
  status: "open" | "closed" | "flagged";
  highlight: boolean;
  started_at: string;
  last_message_at: string | null;
  closed_at: string | null;
  summary: string | null;
};

export type Message = {
  id: string;
  conversation_id: string;
  direction: "in" | "out";
  kind: "text" | "audio" | "image" | "sticker" | "system";
  wa_message_id: string | null;
  text: string | null;
  transcript: string | null;
  audio_path: string | null;
  audio_duration_seconds: number | null;
  latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cost_usd: number | null;
  error: string | null;
  created_at: string;
};
