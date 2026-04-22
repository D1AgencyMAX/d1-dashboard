// Character brain: turns a conversation history into the next reply.
// Uses the Anthropic Messages API directly so we don't pull the SDK.
// Prompt caching is applied to the (long, static) system prompt so every
// turn after the first costs ~10% of the full input price.

import type { Character, Message } from "./types";

type AnthropicContentBlock =
  | { type: "text"; text: string; cache_control?: { type: "ephemeral" } };

type AnthropicMessage = {
  role: "user" | "assistant";
  content: string | AnthropicContentBlock[];
};

type AnthropicResponse = {
  id: string;
  content: Array<{ type: string; text?: string }>;
  usage: {
    input_tokens: number;
    output_tokens: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
  stop_reason: string;
};

export const SAFETY_SENTINEL = "[END_CALL]";

export type BrainReply = {
  text: string;
  shouldEndCharacter: boolean;
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  latencyMs: number;
};

// Sonnet 4.6 pricing, USD per million tokens.
// Cached reads are 10% of the base input price.
const PRICE_TABLE: Record<string, { in: number; out: number }> = {
  "claude-sonnet-4-6": { in: 3.0, out: 15.0 },
  "claude-opus-4-7": { in: 15.0, out: 75.0 },
  "claude-haiku-4-5-20251001": { in: 1.0, out: 5.0 },
};

function priceFor(model: string) {
  return PRICE_TABLE[model] ?? PRICE_TABLE["claude-sonnet-4-6"];
}

function calcCost(
  model: string,
  usage: AnthropicResponse["usage"],
): number {
  const p = priceFor(model);
  const freshInput = usage.input_tokens;
  const cacheCreate = usage.cache_creation_input_tokens ?? 0;
  const cacheRead = usage.cache_read_input_tokens ?? 0;
  const inputCost =
    (freshInput * p.in) / 1_000_000 +
    (cacheCreate * p.in * 1.25) / 1_000_000 +
    (cacheRead * p.in * 0.1) / 1_000_000;
  const outputCost = (usage.output_tokens * p.out) / 1_000_000;
  return Number((inputCost + outputCost).toFixed(6));
}

// Oldest first. Returns Anthropic-shaped message list.
export function historyToMessages(history: Message[]): AnthropicMessage[] {
  const out: AnthropicMessage[] = [];
  for (const m of history) {
    if (m.kind === "system") continue;
    const content = m.text ?? m.transcript ?? "";
    if (!content.trim()) continue;
    out.push({
      role: m.direction === "in" ? "user" : "assistant",
      content,
    });
  }
  return out;
}

export async function generateReply(
  character: Character,
  history: Message[],
  latestUserText: string,
): Promise<BrainReply> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY not set");

  const model = character.model || "claude-sonnet-4-6";

  const systemBlocks: AnthropicContentBlock[] = [
    {
      type: "text",
      text: character.system_prompt,
      cache_control: { type: "ephemeral" },
    },
  ];

  const messages = historyToMessages(history);
  messages.push({ role: "user", content: latestUserText });

  const start = Date.now();
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model,
      max_tokens: character.max_output_tokens,
      temperature: character.temperature,
      system: systemBlocks,
      messages,
    }),
  });
  const latencyMs = Date.now() - start;
  const json = (await res.json().catch(() => ({}))) as AnthropicResponse & { error?: unknown };
  if (!res.ok) {
    throw new Error(`Anthropic error ${res.status}: ${JSON.stringify(json)}`);
  }

  const text = json.content
    .map((b) => (b.type === "text" ? (b.text ?? "") : ""))
    .join("")
    .trim();

  const shouldEndCharacter = text.includes(SAFETY_SENTINEL);
  const cleaned = shouldEndCharacter
    ? text.replace(SAFETY_SENTINEL, "").trim()
    : text;

  return {
    text: cleaned,
    shouldEndCharacter,
    inputTokens: json.usage.input_tokens + (json.usage.cache_read_input_tokens ?? 0),
    outputTokens: json.usage.output_tokens,
    costUsd: calcCost(model, json.usage),
    latencyMs,
  };
}
