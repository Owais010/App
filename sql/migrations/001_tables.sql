-- ============================================================================
-- Quiz Engine & ML Logic - Database Schema
-- Version: 1.0.0
-- Author: Person 2 - Quiz Engine Team
-- Date: 2026-03-01
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. PROFILES (extends auth.users)
-- ============================================================================
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name TEXT,
  target_role TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name)
  VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- 2. SUBJECTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS subjects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  icon TEXT,
  has_levels BOOLEAN DEFAULT TRUE, -- FALSE for single-playlist subjects (Verbal, Quant, Logical)
  display_order INT DEFAULT 100,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 3. TOPICS
-- ============================================================================
CREATE TABLE IF NOT EXISTS topics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  description TEXT,
  weight INT DEFAULT 1, -- For weighted sampling
  difficulty_level TEXT CHECK (difficulty_level IN ('foundational', 'core', 'advanced')),
  prerequisites UUID[], -- Array of topic IDs
  display_order INT DEFAULT 100,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (subject_id, slug)
);

-- ============================================================================
-- 4. QUESTIONS
-- ============================================================================
CREATE TABLE IF NOT EXISTS questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
  difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  correct_option TEXT NOT NULL CHECK (correct_option IN ('A', 'B', 'C', 'D')),
  explanation TEXT,
  tags TEXT[], -- For flexible categorization
  generation_source TEXT CHECK (generation_source IN ('ai', 'manual', 'imported')),
  quality_score NUMERIC(3,2) DEFAULT 1.00, -- 0.00 to 1.00
  times_shown INT DEFAULT 0,
  times_correct INT DEFAULT 0,
  avg_time_seconds NUMERIC(6,2),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 5. ASSESSMENTS
-- ============================================================================
CREATE TABLE IF NOT EXISTS assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  assessment_type TEXT NOT NULL CHECK (assessment_type IN ('diagnostic', 'practice', 'retest', 'custom')),
  status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned')) DEFAULT 'pending',
  blueprint_config JSONB, -- Stores the blueprint used for generation
  total_questions INT DEFAULT 0,
  answered_questions INT DEFAULT 0,
  score INT DEFAULT 0,
  weighted_score NUMERIC DEFAULT 0,
  time_limit_seconds INT,
  time_spent_seconds INT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 6. ASSESSMENT_QUESTIONS (Question Snapshot)
-- ============================================================================
CREATE TABLE IF NOT EXISTS assessment_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  question_order INT NOT NULL,
  question_snapshot JSONB NOT NULL, -- Immutable copy of question at time of assessment
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (assessment_id, question_order)
);

-- ============================================================================
-- 7. USER_ANSWERS
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  assessment_id UUID NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
  assessment_question_id UUID REFERENCES assessment_questions(id) ON DELETE CASCADE,
  question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
  subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
  selected_option TEXT CHECK (selected_option IN ('A', 'B', 'C', 'D', NULL)), -- NULL if skipped
  is_correct BOOLEAN,
  is_skipped BOOLEAN DEFAULT FALSE,
  difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
  time_taken_seconds NUMERIC(8,2),
  confidence_rating NUMERIC(3,2), -- 0.00 to 1.00 (optional user input)
  answered_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 8. USER_TOPIC_STATS (Core ML/Analytics Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_topic_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
  
  -- Raw counters
  attempts INT DEFAULT 0,
  correct INT DEFAULT 0,
  skipped INT DEFAULT 0,
  
  -- Weighted metrics
  weighted_score NUMERIC DEFAULT 0,
  max_possible_weighted NUMERIC DEFAULT 0, -- For normalized accuracy
  
  -- Computed metrics
  accuracy NUMERIC(5,4) DEFAULT 0, -- 0.0000 to 1.0000
  weighted_accuracy NUMERIC(5,4) DEFAULT 0,
  smoothed_accuracy NUMERIC(5,4) DEFAULT 0, -- Laplace smoothed
  
  -- Level classification
  level TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced')),
  level_confidence NUMERIC(3,2) DEFAULT 0, -- 0.00 to 1.00
  
  -- Streak and engagement
  current_streak INT DEFAULT 0,
  best_streak INT DEFAULT 0,
  avg_time_per_question NUMERIC(6,2),
  
  -- Timestamps
  first_attempt_at TIMESTAMPTZ,
  last_attempt_at TIMESTAMPTZ,
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (user_id, topic_id)
);

-- ============================================================================
-- 9. USER_SUBJECT_STATS (Aggregate per Subject)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_subject_stats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  total_attempts INT DEFAULT 0,
  total_correct INT DEFAULT 0,
  accuracy NUMERIC(5,4) DEFAULT 0,
  level TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced')),
  topics_attempted INT DEFAULT 0,
  topics_mastered INT DEFAULT 0, -- Topics with level = 'advanced'
  
  last_updated TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, subject_id)
);

-- ============================================================================
-- 10. LEARNING_RESOURCES
-- ============================================================================
CREATE TABLE IF NOT EXISTS learning_resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL, -- NULL for subject-level resources
  level TEXT CHECK (level IN ('beginner', 'intermediate', 'advanced', NULL)), -- NULL for single-playlist
  
  title TEXT NOT NULL,
  description TEXT,
  resource_type TEXT CHECK (resource_type IN ('youtube_playlist', 'youtube_video', 'article', 'course', 'book')),
  youtube_url TEXT,
  thumbnail_url TEXT,
  duration_minutes INT,
  
  priority INT DEFAULT 100, -- Lower = higher priority
  quality_score NUMERIC(3,2) DEFAULT 1.00,
  view_count INT DEFAULT 0,
  completion_rate NUMERIC(3,2) DEFAULT 0,
  
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 11. RECOMMENDATIONS (Analytics/Tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  assessment_id UUID REFERENCES assessments(id) ON DELETE SET NULL,
  topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
  subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
  resource_id UUID REFERENCES learning_resources(id) ON DELETE SET NULL,
  
  reason TEXT,
  accuracy_at_recommendation NUMERIC(5,4),
  level_at_recommendation TEXT,
  
  is_viewed BOOLEAN DEFAULT FALSE,
  is_started BOOLEAN DEFAULT FALSE,
  is_completed BOOLEAN DEFAULT FALSE,
  
  viewed_at TIMESTAMPTZ,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 12. ASSESSMENT_BLUEPRINTS (Configurable)
-- ============================================================================
CREATE TABLE IF NOT EXISTS assessment_blueprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  assessment_type TEXT NOT NULL CHECK (assessment_type IN ('diagnostic', 'practice', 'retest', 'custom')),
  description TEXT,
  
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  -- Config structure:
  -- {
  --   "numQuestions": 30,
  --   "difficultyDistribution": { "easy": 0.4, "medium": 0.4, "hard": 0.2 },
  --   "subjectStrategy": "all" | "topic-focused" | "weak-priority",
  --   "topicShare": 0.6,
  --   "excludeRecentDays": 90,
  --   "excludeRecentCount": 200,
  --   "timeLimitSeconds": 2700
  -- }
  
  is_default BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- 13. ANALYTICS_EVENTS (For Observability)
-- ============================================================================
CREATE TABLE IF NOT EXISTS analytics_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL, -- 'assessment_started', 'assessment_completed', 'recommendation_clicked', etc.
  event_data JSONB DEFAULT '{}'::jsonb,
  session_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_topic_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_subject_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Public read access for reference tables
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_blueprints ENABLE ROW LEVEL SECURITY;

-- Profiles: users can only access their own profile
CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Assessments: users can access their own assessments
CREATE POLICY "Users can view own assessments" ON assessments FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own assessments" ON assessments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own assessments" ON assessments FOR UPDATE USING (auth.uid() = user_id);

-- User answers: users can access their own answers
CREATE POLICY "Users can view own answers" ON user_answers FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own answers" ON user_answers FOR INSERT WITH CHECK (auth.uid() = user_id);

-- User topic stats: users can view their own stats
CREATE POLICY "Users can view own topic stats" ON user_topic_stats FOR SELECT USING (auth.uid() = user_id);

-- User subject stats: users can view their own stats
CREATE POLICY "Users can view own subject stats" ON user_subject_stats FOR SELECT USING (auth.uid() = user_id);

-- Recommendations: users can access their own recommendations
CREATE POLICY "Users can view own recommendations" ON recommendations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own recommendations" ON recommendations FOR UPDATE USING (auth.uid() = user_id);

-- Analytics events: users can insert their own events
CREATE POLICY "Users can insert own events" ON analytics_events FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Public read access for reference data
CREATE POLICY "Public read subjects" ON subjects FOR SELECT USING (is_active = TRUE);
CREATE POLICY "Public read topics" ON topics FOR SELECT USING (is_active = TRUE);
CREATE POLICY "Public read questions" ON questions FOR SELECT USING (is_active = TRUE);
CREATE POLICY "Public read resources" ON learning_resources FOR SELECT USING (is_active = TRUE);
CREATE POLICY "Public read blueprints" ON assessment_blueprints FOR SELECT USING (is_active = TRUE);
