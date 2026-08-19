-- ==============================================================================
-- Migration: 003_progression.sql
-- Description: Progression, In-Level Word Queue, and Lock State Tracking Schema
-- Phase: 3 (Progression, Skip/Retry Queue, Authorized Word Override)
-- ==============================================================================

-- 1. Student Progress (Per-Level lock/completion state)
create table if not exists public.student_progress (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references auth.users(id) on delete cascade,
  level_id uuid not null references public.levels(id) on delete cascade,
  status text not null default 'locked' check (status in ('locked', 'unlocked', 'completed')),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (student_id, level_id)
);

-- 2. World Progress (Per-World lock/completion state for journey & map)
create table if not exists public.world_progress (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references auth.users(id) on delete cascade,
  world_id uuid not null references public.worlds(id) on delete cascade,
  status text not null default 'locked' check (status in ('locked', 'unlocked', 'completed')),
  unlocked_at timestamptz default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (student_id, world_id)
);

-- 3. Word Progress (In-Level Active Queue, Skip/Retry state & Attempts)
create table if not exists public.word_progress (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references auth.users(id) on delete cascade,
  level_id uuid not null references public.levels(id) on delete cascade,
  word_id uuid not null references public.words(id) on delete restrict,
  status text not null default 'pending' check (status in ('pending', 'completed', 'skipped', 'resolved_by_override')),
  attempt_count int not null default 0,
  queue_order int not null default 1, -- Tracks dynamic sequence within active level queue
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (student_id, level_id, word_id)
);

-- 4. Performance Indexes
create index if not exists idx_student_progress_student on public.student_progress (student_id);
create index if not exists idx_student_progress_level on public.student_progress (level_id);
create index if not exists idx_world_progress_student on public.world_progress (student_id);
create index if not exists idx_world_progress_world on public.world_progress (world_id);
create index if not exists idx_word_progress_student_level on public.word_progress (student_id, level_id);
create index if not exists idx_word_progress_status on public.word_progress (status);

-- 5. Updated_At Triggers
drop trigger if exists trigger_student_progress_updated_at on public.student_progress;
create trigger trigger_student_progress_updated_at
  before update on public.student_progress
  for each row
  execute function public.handle_updated_at();

drop trigger if exists trigger_world_progress_updated_at on public.world_progress;
create trigger trigger_world_progress_updated_at
  before update on public.world_progress
  for each row
  execute function public.handle_updated_at();

drop trigger if exists trigger_word_progress_updated_at on public.word_progress;
create trigger trigger_word_progress_updated_at
  before update on public.word_progress
  for each row
  execute function public.handle_updated_at();

-- 6. Row Level Security (RLS)
alter table public.student_progress enable row level security;
alter table public.world_progress enable row level security;
alter table public.word_progress enable row level security;

-- Drop existing policies if re-running migration
drop policy if exists "Students can view own progress" on public.student_progress;
drop policy if exists "Students can insert own progress" on public.student_progress;
drop policy if exists "Students can update own progress" on public.student_progress;

drop policy if exists "Students can view own world progress" on public.world_progress;
drop policy if exists "Students can insert own world progress" on public.world_progress;
drop policy if exists "Students can update own world progress" on public.world_progress;

drop policy if exists "Students can view own word progress" on public.word_progress;
drop policy if exists "Students can insert own word progress" on public.word_progress;
drop policy if exists "Students can update own word progress" on public.word_progress;

-- Student Progress Policies
create policy "Students can view own progress"
  on public.student_progress for select
  using (auth.uid() = student_id);

create policy "Students can insert own progress"
  on public.student_progress for insert
  with check (auth.uid() = student_id);

create policy "Students can update own progress"
  on public.student_progress for update
  using (auth.uid() = student_id)
  with check (auth.uid() = student_id);

-- World Progress Policies
create policy "Students can view own world progress"
  on public.world_progress for select
  using (auth.uid() = student_id);

create policy "Students can insert own world progress"
  on public.world_progress for insert
  with check (auth.uid() = student_id);

create policy "Students can update own world progress"
  on public.world_progress for update
  using (auth.uid() = student_id)
  with check (auth.uid() = student_id);

-- Word Progress Policies
create policy "Students can view own word progress"
  on public.word_progress for select
  using (auth.uid() = student_id);

create policy "Students can insert own word progress"
  on public.word_progress for insert
  with check (auth.uid() = student_id);

create policy "Students can update own word progress"
  on public.word_progress for update
  using (auth.uid() = student_id)
  with check (auth.uid() = student_id);

-- NOTE: No DELETE policies are granted to student role.
