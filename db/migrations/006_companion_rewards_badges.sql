-- ==============================================================================
-- Migration 006: Companion, Treasure, Rewards, Badges & Mystery Events Schema
-- Phase: 9 (Gamification: Companion Evolution, Rewards, Badges, Mystery)
-- ==============================================================================

-- 1. Student Companion Table
CREATE TABLE IF NOT EXISTS public.student_companion (
    student_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    stage text NOT NULL DEFAULT 'egg' CHECK (stage IN ('egg', 'baby_bird', 'blue_bird', 'eagle', 'phoenix', 'golden_phoenix')),
    xp int NOT NULL DEFAULT 0 CHECK (xp >= 0),
    updated_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Companion XP Events (Persistent Idempotency Guard for XP Awards)
CREATE TABLE IF NOT EXISTS public.companion_xp_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_key text NOT NULL,
    xp_awarded int NOT NULL,
    created_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_companion_xp_events UNIQUE (student_id, event_key)
);

-- 2. Rewards Catalog Table (Public-read content)
CREATE TABLE IF NOT EXISTS public.rewards (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type text NOT NULL CHECK (type IN ('avatar', 'background', 'sticker', 'accessory', 'title', 'effect')),
    name text NOT NULL,
    asset_ref text NOT NULL,
    rarity text NOT NULL CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),
    created_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_rewards_name UNIQUE (name)
);

-- 3. Student Owned Rewards Table
CREATE TABLE IF NOT EXISTS public.student_rewards (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    reward_id uuid NOT NULL REFERENCES public.rewards(id) ON DELETE CASCADE,
    source text NOT NULL CHECK (source IN ('treasure', 'badge', 'starter', 'level_reward')),
    earned_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    equipped boolean NOT NULL DEFAULT false,
    CONSTRAINT uq_student_rewards UNIQUE (student_id, reward_id)
);

-- 4. Badges Catalog Table (Public-read content)
CREATE TABLE IF NOT EXISTS public.badges (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    key text NOT NULL UNIQUE,
    name text NOT NULL,
    description text NOT NULL,
    criteria_type text NOT NULL CHECK (criteria_type IN ('first_word', 'perfect_score', 'total_words', 'streak', 'speed', 'world_complete', 'mastery')),
    criteria_value int NOT NULL DEFAULT 1,
    icon_emoji text NOT NULL DEFAULT '🏅',
    created_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 5. Student Owned Badges Table
CREATE TABLE IF NOT EXISTS public.student_badges (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    badge_id uuid NOT NULL REFERENCES public.badges(id) ON DELETE CASCADE,
    earned_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_student_badges UNIQUE (student_id, badge_id)
);

-- 6. Treasure Events Table (Idempotency Guard for Level Chests)
CREATE TABLE IF NOT EXISTS public.treasure_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    level_id uuid NOT NULL REFERENCES public.levels(id) ON DELETE CASCADE,
    reward_id uuid REFERENCES public.rewards(id) ON DELETE SET NULL,
    opened_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_treasure_events UNIQUE (student_id, level_id)
);

-- 7. Mystery Surprise Events Table (Idempotency Guard for Mystery Surprises)
CREATE TABLE IF NOT EXISTS public.mystery_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    level_id uuid NOT NULL REFERENCES public.levels(id) ON DELETE CASCADE,
    surprise_key text NOT NULL,
    triggered_at timestamptz NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_mystery_events UNIQUE (student_id, level_id)
);

-- ==============================================================================
-- 8. Enable Row Level Security (RLS)
-- ==============================================================================
ALTER TABLE public.student_companion ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companion_xp_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_rewards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_badges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.treasure_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mystery_events ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if re-running
DROP POLICY IF EXISTS "Students can view own companion" ON public.student_companion;
DROP POLICY IF EXISTS "Students can insert own companion" ON public.student_companion;
DROP POLICY IF EXISTS "Students can update own companion" ON public.student_companion;
DROP POLICY IF EXISTS "Students can view own xp events" ON public.companion_xp_events;
DROP POLICY IF EXISTS "Students can insert own xp events" ON public.companion_xp_events;
DROP POLICY IF EXISTS "Public rewards are viewable by authenticated users" ON public.rewards;
DROP POLICY IF EXISTS "Public rewards are viewable by anon" ON public.rewards;
DROP POLICY IF EXISTS "Students can view own rewards" ON public.student_rewards;
DROP POLICY IF EXISTS "Students can insert own rewards" ON public.student_rewards;
DROP POLICY IF EXISTS "Students can update own reward equipped status" ON public.student_rewards;
DROP POLICY IF EXISTS "Public badges are viewable by authenticated users" ON public.badges;
DROP POLICY IF EXISTS "Public badges are viewable by anon" ON public.badges;
DROP POLICY IF EXISTS "Students can view own badges" ON public.student_badges;
DROP POLICY IF EXISTS "Students can insert own badges" ON public.student_badges;
DROP POLICY IF EXISTS "Students can view own treasure events" ON public.treasure_events;
DROP POLICY IF EXISTS "Students can insert own treasure events" ON public.treasure_events;
DROP POLICY IF EXISTS "Students can view own mystery events" ON public.mystery_events;
DROP POLICY IF EXISTS "Students can insert own mystery events" ON public.mystery_events;

-- Student Companion Policies
CREATE POLICY "Students can view own companion"
    ON public.student_companion FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own companion"
    ON public.student_companion FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

CREATE POLICY "Students can update own companion"
    ON public.student_companion FOR UPDATE
    TO authenticated
    USING (auth.uid() = student_id)
    WITH CHECK (auth.uid() = student_id);

-- Companion XP Events Policies
CREATE POLICY "Students can view own xp events"
    ON public.companion_xp_events FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own xp events"
    ON public.companion_xp_events FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

-- Rewards Catalog Policies
CREATE POLICY "Public rewards are viewable by authenticated users"
    ON public.rewards FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Public rewards are viewable by anon"
    ON public.rewards FOR SELECT
    TO anon
    USING (true);

-- Student Rewards Policies
CREATE POLICY "Students can view own rewards"
    ON public.student_rewards FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own rewards"
    ON public.student_rewards FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

CREATE POLICY "Students can update own reward equipped status"
    ON public.student_rewards FOR UPDATE
    TO authenticated
    USING (auth.uid() = student_id)
    WITH CHECK (auth.uid() = student_id);

-- Badges Catalog Policies
CREATE POLICY "Public badges are viewable by authenticated users"
    ON public.badges FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Public badges are viewable by anon"
    ON public.badges FOR SELECT
    TO anon
    USING (true);

-- Student Badges Policies
CREATE POLICY "Students can view own badges"
    ON public.student_badges FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own badges"
    ON public.student_badges FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

-- Treasure Events Policies
CREATE POLICY "Students can view own treasure events"
    ON public.treasure_events FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own treasure events"
    ON public.treasure_events FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

-- Mystery Events Policies
CREATE POLICY "Students can view own mystery events"
    ON public.mystery_events FOR SELECT
    TO authenticated
    USING (auth.uid() = student_id);

CREATE POLICY "Students can insert own mystery events"
    ON public.mystery_events FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = student_id);

-- ==============================================================================
-- 9. Seed Rewards Catalog (12 Cosmetic Rewards across 6 Types)
-- ==============================================================================
INSERT INTO public.rewards (type, name, asset_ref, rarity)
VALUES
    ('avatar', 'Golden Adventurer Cap', 'assets/rewards/avatar_gold_cap.webp', 'rare'),
    ('avatar', 'Sound Master Headphones', 'assets/rewards/avatar_headphones.webp', 'epic'),
    ('background', 'Starry Sky Realm', 'assets/rewards/bg_starry_sky.webp', 'rare'),
    ('background', 'Crystal Cavern Glow', 'assets/rewards/bg_crystal_cavern.webp', 'epic'),
    ('sticker', 'Fire Phoenix Crest', 'assets/rewards/sticker_phoenix.webp', 'legendary'),
    ('sticker', 'Emerald Leaf Emblem', 'assets/rewards/sticker_leaf.webp', 'common'),
    ('accessory', 'Mystic Microphone', 'assets/rewards/acc_mystic_mic.webp', 'rare'),
    ('accessory', 'Champion Cape', 'assets/rewards/acc_champion_cape.webp', 'epic'),
    ('title', 'Phonetic Pioneer', 'assets/rewards/title_pioneer.webp', 'common'),
    ('title', 'Realm Sovereign', 'assets/rewards/title_sovereign.webp', 'legendary'),
    ('effect', 'Rainbow Sparkle Trail', 'assets/rewards/effect_sparkle.webp', 'epic'),
    ('effect', 'Golden Aureole', 'assets/rewards/effect_golden_glow.webp', 'legendary')
ON CONFLICT (name) DO UPDATE SET
    type = EXCLUDED.type,
    asset_ref = EXCLUDED.asset_ref,
    rarity = EXCLUDED.rarity;

-- ==============================================================================
-- 10. Seed Approved Badges (8 Core Achievement Badges)
-- ==============================================================================
INSERT INTO public.badges (key, name, description, criteria_type, criteria_value, icon_emoji)
VALUES
    ('first_words', 'First Words', 'Pronounce your first word correctly in an adventure.', 'first_word', 1, '🌱'),
    ('perfect_pronunciation', 'Perfect Pronunciation', 'Achieve a 100% pronunciation score on any target word.', 'perfect_score', 100, '🎯'),
    ('words_50', '50 Correct Words', 'Successfully pronounce 50 total words across your journey.', 'total_words', 50, '📚'),
    ('words_100', '100 Correct Words', 'Master 100 total words in Pronunciation Adventure.', 'total_words', 100, '👑'),
    ('streak_5', '5-Day Streak', 'Maintain a pronunciation streak of 5 consecutive words without mistakes.', 'streak', 5, '🔥'),
    ('fast_speaker', 'Fast Speaker', 'Complete a level attempt with rapid, accurate pronunciation.', 'speed', 1, '⚡'),
    ('word_master', 'Word Master', 'Finish an entire 7-word level with a flawless 3-star rating.', 'mastery', 7, '🌟'),
    ('language_explorer', 'Language Explorer', 'Conquer your first entire adventure world realm.', 'world_complete', 1, '🧭')
ON CONFLICT (key) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    criteria_type = EXCLUDED.criteria_type,
    criteria_value = EXCLUDED.criteria_value,
    icon_emoji = EXCLUDED.icon_emoji;
