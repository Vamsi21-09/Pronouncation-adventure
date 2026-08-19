-- ==============================================================================
-- Migration 005: Score, Streak, and Level Results Schema
-- Purpose: Extend profiles with total_score, current_streak, and best_streak;
--          Add level_results table for idempotent completion tracking and stars.
-- ==============================================================================

-- 1. Extend profiles table with score and streak columns
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS total_score int NOT NULL DEFAULT 0;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS current_streak int NOT NULL DEFAULT 0;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS best_streak int NOT NULL DEFAULT 0;

-- 2. Create level_results table
CREATE TABLE IF NOT EXISTS public.level_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    level_id uuid NOT NULL REFERENCES public.levels(id) ON DELETE CASCADE,
    score int NOT NULL DEFAULT 0,
    accuracy numeric(5,2) NOT NULL DEFAULT 0.0,
    words_completed int NOT NULL DEFAULT 0,
    mistakes int NOT NULL DEFAULT 0,
    streak_at_completion int NOT NULL DEFAULT 0,
    stars int NOT NULL DEFAULT 1 CHECK (stars >= 1 AND stars <= 3),
    completed_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT level_results_student_level_key UNIQUE (student_id, level_id)
);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.level_results ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for level_results
-- Students can select their own completion results
DROP POLICY IF EXISTS "Students can view own level results" ON public.level_results;
CREATE POLICY "Students can view own level results"
    ON public.level_results
    FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

-- Students can insert their own completion results
DROP POLICY IF EXISTS "Students can insert own level results" ON public.level_results;
CREATE POLICY "Students can insert own level results"
    ON public.level_results
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

-- No update/delete policies for authenticated users (results are immutable historical records)
