-- ==============================================================================
-- Migration: 001_init_auth_and_profiles.sql
-- Description: Initial schema for Supabase Auth integration, student profiles,
--              Row-Level Security (RLS), and audit logging foundations.
-- Phase: 1 (Project Foundation & Profiles)
-- ==============================================================================

-- 1. Create profiles table linked to auth.users
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text unique not null,
  display_name text,
  role text not null default 'student' check (role in ('student', 'teacher', 'admin')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Index for fast username lookups and profile queries
create index if not exists idx_profiles_username on public.profiles (username);

-- 2. Timestamp update helper trigger
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trigger_profiles_updated_at on public.profiles;
create trigger trigger_profiles_updated_at
  before update on public.profiles
  for each row
  execute function public.handle_updated_at();

-- 3. Security Trigger: Prevent Self-Escalation of Role
-- Ensures that students cannot modify their own role from 'student' to 'teacher' or 'admin'.
-- Privileged role updates can only be executed via service_role / administrative functions.
create or replace function public.prevent_role_self_escalation()
returns trigger as $$
begin
  if (auth.uid() = old.id and new.role is distinct from old.role) then
    -- Check if execution is coming from a non-service_role context
    if (auth.jwt() ->> 'role') is distinct from 'service_role' then
      raise exception 'Unauthorized role modification: Users cannot escalate their own role.';
    end if;
  end if;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists trigger_prevent_role_self_escalation on public.profiles;
create trigger trigger_prevent_role_self_escalation
  before update on public.profiles
  for each row
  execute function public.prevent_role_self_escalation();

-- 4. Enable Row Level Security (RLS) on profiles
alter table public.profiles enable row level security;

-- Drop existing policies if re-running migration
drop policy if exists "Users can view own profile" on public.profiles;
drop policy if exists "Users can insert own profile" on public.profiles;
drop policy if exists "Users can update own profile" on public.profiles;

-- RLS Policy: Users can view only their own profile
create policy "Users can view own profile"
  on public.profiles
  for select
  using (auth.uid() = id);

-- RLS Policy: Users can insert their own profile upon signup
create policy "Users can insert own profile"
  on public.profiles
  for insert
  with check (auth.uid() = id);

-- RLS Policy: Users can update their own profile (display_name, etc.)
create policy "Users can update own profile"
  on public.profiles
  for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- NOTE: No DELETE policy is provided. Regular users cannot delete their profile from client.


-- ==============================================================================
-- 5. Foundation for Future Authorized Word Override System
-- ==============================================================================
-- This table stores audit records whenever a teacher/admin authorizes overriding
-- a word during gameplay (e.g. when hardware/mic misrecognition blocks a student).
--
-- NOTE: word_id and level_id are nullable UUIDs in this migration and will be
-- linked via ALTER TABLE ... ADD CONSTRAINT FOREIGN KEY in Phase 2 once the
-- content schema (words and levels tables) is deployed.
-- ==============================================================================

create table if not exists public.override_audit_log (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references auth.users(id),
  word_id uuid,          -- FK to words.id will be added in Phase 2 content migration
  level_id uuid,         -- FK to levels.id will be added in Phase 2 content migration
  authorized_by uuid not null references auth.users(id), -- Teacher/Admin profile id
  override_type text not null default 'authorized_override',
  reason text,
  created_at timestamptz not null default now()
);

-- Index for auditing by student and authorizer
create index if not exists idx_override_audit_student on public.override_audit_log (student_id);
create index if not exists idx_override_audit_authorizer on public.override_audit_log (authorized_by);

-- Enable RLS on override_audit_log
alter table public.override_audit_log enable row level security;

-- By default, no client-side SELECT, INSERT, UPDATE, or DELETE policies are granted.
-- Regular users (using the anon key) cannot read or write to this table directly.
-- Override records will be generated exclusively via a secure server-side routine
-- or teacher-authorized stored procedure in future gameplay phases.
