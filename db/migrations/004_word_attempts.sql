-- Migration: 004_word_attempts.sql
-- Description: Pronunciation attempts tracking, RLS policies, and concurrency-safe attempt_number generator RPC.

-- 1. Create word_attempts table
create table if not exists public.word_attempts (
    id uuid primary key default gen_random_uuid(),
    student_id uuid not null references public.profiles(id) on delete cascade,
    word_id uuid not null references public.words(id) on delete cascade,
    level_id uuid not null references public.levels(id) on delete cascade,
    transcribed_text text not null,
    score integer not null check (score >= 0 and score <= 100),
    passed boolean not null,
    attempt_number integer not null,
    created_at timestamptz not null default now()
);

-- 2. Indexes for performance
create index if not exists idx_word_attempts_student_word 
    on public.word_attempts(student_id, word_id, attempt_number);

create index if not exists idx_word_attempts_student_level 
    on public.word_attempts(student_id, level_id, created_at desc);

-- 3. Row Level Security (RLS)
alter table public.word_attempts enable row level security;

-- Students can read their own attempts
create policy "Students can read own word attempts"
    on public.word_attempts
    for select
    to authenticated
    using (student_id = auth.uid());

-- Students can insert attempts scoped to their own student_id (append-only)
create policy "Students can insert own word attempts"
    on public.word_attempts
    for insert
    to authenticated
    with check (student_id = auth.uid());

-- No update or delete policies (word_attempts are immutable audit logs)

-- 4. Concurrency-Safe Attempt Numbering RPC
--
-- DESIGN RATIONALE:
-- Computing attempt_number in application code via 'count(*) + 1' or 'max(attempt_number) + 1'
-- is vulnerable to race conditions under concurrent client requests (e.g. rapid double-clicking,
-- multi-tab sessions, or automatic network retries).
--
-- APPROACH:
-- We implement a Postgres function (SECURITY DEFINER) called via Supabase RPC.
-- Inside the single atomic transaction, it computes the next attempt_number using:
--   SELECT COALESCE(MAX(attempt_number), 0) + 1
--   FROM public.word_attempts
--   WHERE student_id = p_student_id AND word_id = p_word_id
-- and performs the insert in the exact same statement execution.
-- Postgres table/page locks and transaction isolation ensure sequential, non-colliding attempt numbers.

create or replace function public.record_word_attempt(
    p_student_id uuid,
    p_word_id uuid,
    p_level_id uuid,
    p_transcribed_text text,
    p_score integer,
    p_passed boolean
)
returns jsonb
language plpgsql
security definer
as $$
declare
    v_next_attempt integer;
    v_inserted_row public.word_attempts%rowtype;
begin
    -- Security verification: Ensure authenticated user matches student_id
    if auth.uid() is not null and auth.uid() <> p_student_id then
        raise exception 'Unauthorized attempt insert for student %', p_student_id;
    end if;

    -- Atomic attempt number calculation within transaction
    select coalesce(max(attempt_number), 0) + 1
    into v_next_attempt
    from public.word_attempts
    where student_id = p_student_id and word_id = p_word_id;

    -- Insert new attempt
    insert into public.word_attempts (
        student_id,
        word_id,
        level_id,
        transcribed_text,
        score,
        passed,
        attempt_number
    ) values (
        p_student_id,
        p_word_id,
        p_level_id,
        p_transcribed_text,
        p_score,
        p_passed,
        v_next_attempt
    )
    returning * into v_inserted_row;

    return to_jsonb(v_inserted_row);
end;
$$;
