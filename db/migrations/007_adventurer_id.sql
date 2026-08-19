-- ==============================================================================
-- Migration: 007_adventurer_id.sql
-- Description: 10-digit numeric Adventurer ID support for student profiles.
-- Phase: 10 (Production Refinement)
-- ==============================================================================

-- 1. Add optional persistent adventurer_id column (10 digits numeric string)
alter table public.profiles
  add column if not exists adventurer_id text unique;

-- 2. Index for fast adventurer_id lookups
create index if not exists idx_profiles_adventurer_id on public.profiles (adventurer_id);
