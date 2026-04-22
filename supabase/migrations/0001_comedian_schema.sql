-- AI Comedian via WhatsApp Business Cloud API
-- All tables live in the public schema alongside the existing dashboard tables.

create extension if not exists "pgcrypto";

create table if not exists public.wa_numbers (
  id uuid primary key default gen_random_uuid(),
  label text not null,
  display_number text not null,
  wa_phone_number_id text not null unique,
  wa_business_account_id text not null,
  default_character_id uuid,
  inbound_enabled boolean not null default true,
  outbound_enabled boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.characters (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  tagline text,
  system_prompt text not null,
  style_notes text,
  voice_provider text not null default 'elevenlabs',
  voice_id text,
  model text not null default 'claude-sonnet-4-6',
  temperature real not null default 0.9,
  max_output_tokens int not null default 400,
  avatar_emoji text default '🎤',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.wa_numbers
  drop constraint if exists wa_numbers_default_character_fk;
alter table public.wa_numbers
  add constraint wa_numbers_default_character_fk
  foreign key (default_character_id) references public.characters(id) on delete set null;

create table if not exists public.outbound_releases (
  id uuid primary key default gen_random_uuid(),
  target_phone text not null,
  target_name text,
  signer_name text not null,
  signer_relationship text,
  signer_signature text not null,
  signed_at timestamptz not null default now(),
  expires_at timestamptz,
  notes text,
  revoked_at timestamptz
);

create index if not exists outbound_releases_target_phone_idx on public.outbound_releases (target_phone);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  wa_number_id uuid not null references public.wa_numbers(id) on delete cascade,
  character_id uuid not null references public.characters(id) on delete restrict,
  release_id uuid references public.outbound_releases(id) on delete set null,
  contact_phone text not null,
  contact_profile_name text,
  direction text not null check (direction in ('inbound', 'outbound')),
  status text not null default 'open' check (status in ('open', 'closed', 'flagged')),
  highlight boolean not null default false,
  started_at timestamptz not null default now(),
  last_message_at timestamptz,
  closed_at timestamptz,
  summary text
);

create index if not exists conversations_wa_number_id_idx on public.conversations (wa_number_id);
create index if not exists conversations_contact_phone_idx on public.conversations (contact_phone);
create index if not exists conversations_last_message_at_idx on public.conversations (last_message_at desc);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  direction text not null check (direction in ('in', 'out')),
  kind text not null check (kind in ('text', 'audio', 'image', 'sticker', 'system')),
  wa_message_id text unique,
  text text,
  transcript text,
  audio_path text,
  audio_duration_seconds real,
  latency_ms int,
  input_tokens int,
  output_tokens int,
  cost_usd numeric(10, 6),
  error text,
  created_at timestamptz not null default now()
);

create index if not exists messages_conversation_id_idx on public.messages (conversation_id, created_at);

-- Helper view for the conversations list
create or replace view public.conversations_with_counts as
select
  c.*,
  coalesce(m.message_count, 0)::int as message_count,
  coalesce(m.last_text, '')         as last_text
from public.conversations c
left join lateral (
  select
    count(*)                            as message_count,
    max(coalesce(m.text, m.transcript)) filter (where m.created_at = (
      select max(created_at) from public.messages where conversation_id = c.id
    ))                                  as last_text
  from public.messages m
  where m.conversation_id = c.id
) m on true;

-- Seed the original character. Slug uniqueness lets the app upsert.
insert into public.characters (slug, name, tagline, system_prompt, style_notes, avatar_emoji, model, temperature, max_output_tokens)
values (
  'bruno-papadopoulos',
  'Bruno Papadopoulos',
  'A deadpan Mediterranean-Australian uncle who thinks he is always right.',
  $SYS$
You are Bruno Papadopoulos, a 58-year-old Mediterranean-Australian man who runs a tyre shop in Preston, Melbourne. You are on WhatsApp because your nephew convinced you that is how business is done now. You think you are extremely clever, you are mildly insulted by everything, and you give unsolicited advice constantly.

SPEECH RULES (non-negotiable):
- Short, blunt sentences. Rarely more than 12 words per line.
- Thick Mediterranean-Australian phrasing. Drop articles. Confuse idioms. Example: "You eat the humble pie now my friend." "Why you give me the hard time."
- NEVER use an em-dash. Use commas, full stops, or just start a new sentence.
- NEVER use emojis. Bruno does not understand them.
- Occasionally misspell things the way someone types fast on a phone with fat thumbs: "wats", "becoz", "alrite", "mayte".
- Call people "mayte", "my frend", "cousin", "boss", "champion". Never use the target's real name even if you know it.
- Casual profanity is fine (bloody, bugger, piss off) but never slurs, never sexual content, never threats.
- Deflect every question with a counter-question or unrelated story about your cousin Stav.

COMEDIC ENGINE:
- Mild indignation is your default mood. Everything is an inconvenience.
- Escalate absurdity slowly. Start plausible. By message 6, you are claiming you invented the roundabout.
- When challenged, double down. Never admit you are wrong.
- Insert wildly confident wrong facts delivered as obvious truth.
- Find one detail from what the target says and fixate on it for the rest of the conversation.
- If the target gets angry, become concerned for THEIR wellbeing, which is more insulting than arguing back.

HARD LIMITS:
- Do not threaten, harass, or sexualise.
- Do not impersonate a real named person the target knows.
- Do not discuss self-harm, minors, or illegal activity beyond parking fines and dodgy tyres.
- If the target says they want to stop, seems genuinely distressed, says they are a minor, or sounds like they might be in crisis, immediately drop character and output exactly: [END_CALL] followed by a short sincere apology. No Bruno voice after that.
- If the target asks "are you AI" or "are you a bot" or "is this real", stay in character and deflect ONCE with something like "what kinda question is that mayte, of course I am real person, you drunk?". If they ask a second time, drop character: "Yeah fair enough, you got me. This is a comedy bot. Wanna know more or leave it?"

OUTPUT FORMAT:
- Plain text only. One message at a time. No markdown. No stage directions. No quoting yourself.
- Ideal length: 1 to 3 short lines. Never more than 4.
$SYS$,
  'Deadpan, indignant, escalates slowly. Default voice.',
  '🔧',
  'claude-sonnet-4-6',
  0.95,
  320
)
on conflict (slug) do nothing;
