-- ==============================================================================
-- Migration: 002_content_schema.sql
-- Description: Game Content Schema (Worlds, Levels, Words, Level-Words Junction),
--              indexes, Row-Level Security, and deferred foreign keys on override_audit_log.
-- Phase: 2 (Game Content Foundation)
-- ==============================================================================

-- 1. Worlds Table
create table if not exists public.worlds (
  id uuid primary key default gen_random_uuid(),
  order_index int not null unique,
  name text not null,
  theme_key text not null,       -- e.g. 'village', 'forest' - used for UI styling & themes
  icon_emoji text,                -- e.g. '🏡', '🌲'
  created_at timestamptz not null default now()
);

-- 2. Levels Table
create table if not exists public.levels (
  id uuid primary key default gen_random_uuid(),
  world_id uuid not null references public.worlds(id) on delete cascade,
  order_index int not null,       -- 1-3 for development; 1-30 in production
  difficulty_band text not null check (difficulty_band in ('easy', 'medium', 'hard')),
  created_at timestamptz not null default now(),
  unique (world_id, order_index)
);

-- 3. Words Table (Global Word Bank)
create table if not exists public.words (
  id uuid primary key default gen_random_uuid(),
  text text not null unique,      -- DB-level enforcement of zero duplicate words
  meaning text not null,
  example_sentence text not null,
  pronunciation_hint text not null,
  syllable_breakdown text,        -- e.g. 'gar-den'
  common_mistake text,            -- e.g. 'Dropping the final D sound'
  image_path text,                -- Supabase Storage path/key (e.g. 'words/garden.webp')
  image_alt_text text,            -- Accessibility alt text
  difficulty_band text not null check (difficulty_band in ('easy', 'medium', 'hard')),
  created_at timestamptz not null default now()
);

-- 4. Level-Words Junction Table (Preserves order & supports future optional/bonus words)
create table if not exists public.level_words (
  id uuid primary key default gen_random_uuid(),
  level_id uuid not null references public.levels(id) on delete cascade,
  word_id uuid not null references public.words(id) on delete restrict,
  order_index int not null,        -- Preserves word sequence within the level (1-7)
  is_required boolean not null default true, -- Forward-compatible for bonus words
  created_at timestamptz not null default now(),
  unique (level_id, word_id),
  unique (level_id, order_index)
);

-- 5. Performance Indexes
create index if not exists idx_levels_world_id on public.levels (world_id);
create index if not exists idx_level_words_level_id on public.level_words (level_id);
create index if not exists idx_level_words_word_id on public.level_words (word_id);
create index if not exists idx_words_text on public.words (text);

-- 6. Row Level Security (RLS)
alter table public.worlds enable row level security;
alter table public.levels enable row level security;
alter table public.words enable row level security;
alter table public.level_words enable row level security;

-- Drop existing policies if re-running migration
drop policy if exists "Public worlds are viewable by authenticated users" on public.worlds;
drop policy if exists "Public levels are viewable by authenticated users" on public.levels;
drop policy if exists "Public words are viewable by authenticated users" on public.words;
drop policy if exists "Public level_words are viewable by authenticated users" on public.level_words;

-- Read-only policies for authenticated users
create policy "Public worlds are viewable by authenticated users"
  on public.worlds for select
  to authenticated
  using (true);

create policy "Public levels are viewable by authenticated users"
  on public.levels for select
  to authenticated
  using (true);

create policy "Public words are viewable by authenticated users"
  on public.words for select
  to authenticated
  using (true);

create policy "Public level_words are viewable by authenticated users"
  on public.level_words for select
  to authenticated
  using (true);

-- NOTE: No INSERT, UPDATE, or DELETE policies are granted to the authenticated role.
-- Content mutations are performed exclusively through developer seeding (service_role)
-- or future authorized admin endpoints.

-- 7. Foreign Key Constraints for override_audit_log (Deferred from Phase 1)
-- Now that words and levels exist, link the foreign keys:
do $$
begin
  if exists (select 1 from information_schema.tables where table_name = 'override_audit_log') then
    if not exists (
      select 1 from information_schema.table_constraints
      where constraint_name = 'fk_override_word'
    ) then
      alter table public.override_audit_log
        add constraint fk_override_word foreign key (word_id) references public.words(id);
    end if;

    if not exists (
      select 1 from information_schema.table_constraints
      where constraint_name = 'fk_override_level'
    ) then
      alter table public.override_audit_log
        add constraint fk_override_level foreign key (level_id) references public.levels(id);
    end if;
  end if;
end $$;
