-- Admin permissions for Lesson Factory
GRANT USAGE ON SCHEMA public TO service_role;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- Learner topic state: saves current status and assessment drafts
CREATE TABLE IF NOT EXISTS public.learner_topic_state (
    learner_name TEXT NOT NULL DEFAULT 'Shri',
    topic_id TEXT NOT NULL REFERENCES public.topics(id) ON DELETE CASCADE,
    active_page TEXT NOT NULL DEFAULT 'Lesson',
    status TEXT NOT NULL DEFAULT 'not_started',
    payload JSONB NOT NULL DEFAULT '{}'::JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (learner_name, topic_id)
);

GRANT SELECT, INSERT, UPDATE ON public.learner_topic_state TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.learner_topic_state TO service_role;

ALTER TABLE public.learner_topic_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon can read learner topic state" ON public.learner_topic_state;
CREATE POLICY "anon can read learner topic state"
ON public.learner_topic_state
FOR SELECT
TO anon
USING (true);

DROP POLICY IF EXISTS "anon can insert learner topic state" ON public.learner_topic_state;
CREATE POLICY "anon can insert learner topic state"
ON public.learner_topic_state
FOR INSERT
TO anon
WITH CHECK (true);

DROP POLICY IF EXISTS "anon can update learner topic state" ON public.learner_topic_state;
CREATE POLICY "anon can update learner topic state"
ON public.learner_topic_state
FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);