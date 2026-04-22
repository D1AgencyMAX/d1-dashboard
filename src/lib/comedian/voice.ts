// Speech-to-text + text-to-speech for voice-note conversations on WhatsApp.
// STT: OpenAI Whisper (cheap, good Aussie/Mediterranean accent handling).
// TTS: ElevenLabs (character voice quality). Falls back to silence if unconfigured.

export type TranscribeResult = {
  text: string;
  language?: string;
  durationSeconds?: number;
  costUsd: number;
};

const WHISPER_MODEL = "whisper-1";
// Whisper-1: $0.006 per minute of audio. (Rates current as of 2026.)
const WHISPER_PRICE_PER_MINUTE = 0.006;

export async function transcribeAudio(
  bytes: Uint8Array,
  mimeType: string,
): Promise<TranscribeResult> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("OPENAI_API_KEY not set (needed for voice transcription)");

  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(bytes)], { type: mimeType }), filenameFor(mimeType));
  form.append("model", WHISPER_MODEL);
  form.append("response_format", "verbose_json");

  const res = await fetch("https://api.openai.com/v1/audio/transcriptions", {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
  });
  const json = (await res.json().catch(() => ({}))) as {
    text?: string;
    language?: string;
    duration?: number;
    error?: { message?: string };
  };
  if (!res.ok) {
    throw new Error(`Whisper error ${res.status}: ${json.error?.message ?? JSON.stringify(json)}`);
  }
  const duration = json.duration ?? 0;
  return {
    text: json.text ?? "",
    language: json.language,
    durationSeconds: duration,
    costUsd: Number(((duration / 60) * WHISPER_PRICE_PER_MINUTE).toFixed(6)),
  };
}

function filenameFor(mimeType: string): string {
  if (mimeType.includes("ogg")) return "voice.ogg";
  if (mimeType.includes("mpeg") || mimeType.includes("mp3")) return "voice.mp3";
  if (mimeType.includes("wav")) return "voice.wav";
  if (mimeType.includes("mp4") || mimeType.includes("m4a")) return "voice.m4a";
  return "voice.bin";
}

export type SynthesizeResult = {
  bytes: Uint8Array;
  mimeType: string;
  costUsd: number;
};

// ElevenLabs charges by characters. Multilingual v2: ~$0.30 per 1,000 chars on the Creator tier.
// Using a conservative estimate for the dashboard cost column.
const ELEVENLABS_PRICE_PER_1K_CHARS = 0.3;

// WhatsApp needs OGG Opus; browser <audio> is happier with MP3.
export type TtsFormat = "ogg" | "mp3";

export async function synthesizeSpeech(
  text: string,
  voiceId: string,
  format: TtsFormat = "ogg",
): Promise<SynthesizeResult> {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) throw new Error("ELEVENLABS_API_KEY not set");
  if (!voiceId) throw new Error("voiceId not provided");

  const outputFormat = format === "mp3" ? "mp3_44100_128" : "ogg_opus_48000";
  const mimeType = format === "mp3" ? "audio/mpeg" : "audio/ogg";
  const acceptHeader = format === "mp3" ? "audio/mpeg" : "audio/ogg";

  const res = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=${outputFormat}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": apiKey,
        Accept: acceptHeader,
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_multilingual_v2",
        voice_settings: { stability: 0.45, similarity_boost: 0.75, style: 0.35, use_speaker_boost: true },
      }),
    },
  );
  if (!res.ok) {
    const err = await res.text().catch(() => "");
    throw new Error(`ElevenLabs error ${res.status}: ${err}`);
  }
  const buf = new Uint8Array(await res.arrayBuffer());
  return {
    bytes: buf,
    mimeType,
    costUsd: Number(((text.length / 1000) * ELEVENLABS_PRICE_PER_1K_CHARS).toFixed(6)),
  };
}
