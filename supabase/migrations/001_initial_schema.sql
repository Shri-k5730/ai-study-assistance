CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    onion_layer TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    architect_relevance TEXT NOT NULL,
    higher_systems TEXT[] DEFAULT ARRAY[]::TEXT[],
    lower_foundations TEXT[] DEFAULT ARRAY[]::TEXT[],
    production_risks TEXT[] DEFAULT ARRAY[]::TEXT[],
    glue_before TEXT[] DEFAULT ARRAY[]::TEXT[],
    glue_after TEXT[] DEFAULT ARRAY[]::TEXT[],
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lessons (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    lesson_type TEXT NOT NULL DEFAULT 'normal',
    content JSONB NOT NULL DEFAULT '{}'::JSONB,
    source_links JSONB NOT NULL DEFAULT '[]'::JSONB,
    deeper_reading JSONB NOT NULL DEFAULT '[]'::JSONB,
    status TEXT NOT NULL DEFAULT 'draft',
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    pass_mcq_percent NUMERIC(5,2) NOT NULL DEFAULT 70,
    descriptive_min_stars INT NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assessment_questions (
    id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_type TEXT NOT NULL CHECK (question_type IN ('mcq', 'descriptive')),
    question TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT,
    explanation TEXT,
    is_critical BOOLEAN NOT NULL DEFAULT FALSE,
    rubric JSONB NOT NULL DEFAULT '{}'::JSONB,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    lesson_id TEXT NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    assessment_id TEXT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    learner_name TEXT NOT NULL DEFAULT 'Shri',
    mcq_score_percent NUMERIC(5,2),
    critical_pass BOOLEAN,
    mcq_answers JSONB NOT NULL DEFAULT '[]'::JSONB,
    descriptive_answer TEXT,
    descriptive_stars INT,
    descriptive_feedback TEXT,
    passed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id TEXT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    lesson_id TEXT REFERENCES lessons(id) ON DELETE SET NULL,
    learner_name TEXT NOT NULL DEFAULT 'Shri',
    note_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id TEXT REFERENCES topics(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    resource_type TEXT NOT NULL DEFAULT 'official',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO topics (
    id,
    domain,
    onion_layer,
    title,
    summary,
    architect_relevance,
    higher_systems,
    lower_foundations,
    production_risks,
    glue_before,
    glue_after,
    sort_order
)
VALUES (
    'agentic_ai_control_plane',
    'Agentic AI',
    'Outer layer: Agentic AI',
    'AI Control Plane for Agentic Systems',
    'The control plane is the layer that governs how AI systems behave at runtime: policies, permissions, routing, model choice, tool access, evaluation, audit, and rollback.',
    'An AI architect cares because production behavior is not determined by the model alone. It is shaped by prompts, policies, permissions, tools, memory, evaluators, and runtime controls.',
    ARRAY['Autonomous agents', 'RAG assistants', 'AI copilots', 'Multi-tool workflows'],
    ARRAY['Prompts', 'Context windows', 'Tool calling', 'Evaluators', 'Access control'],
    ARRAY['Silent behavior drift', 'Unsafe tool use', 'Untraceable decisions', 'No rollback path', 'Weak accountability'],
    ARRAY['Prompting', 'Tool calling', 'Evaluation basics'],
    ARRAY['Agent governance', 'Runtime observability', 'AI operating model'],
    10
)
ON CONFLICT (id) DO UPDATE SET
    domain = EXCLUDED.domain,
    onion_layer = EXCLUDED.onion_layer,
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    architect_relevance = EXCLUDED.architect_relevance,
    higher_systems = EXCLUDED.higher_systems,
    lower_foundations = EXCLUDED.lower_foundations,
    production_risks = EXCLUDED.production_risks,
    glue_before = EXCLUDED.glue_before,
    glue_after = EXCLUDED.glue_after,
    sort_order = EXCLUDED.sort_order,
    updated_at = NOW();

INSERT INTO lessons (
    id,
    topic_id,
    title,
    lesson_type,
    content,
    source_links,
    deeper_reading,
    status,
    version
)
VALUES (
    'lesson_agentic_ai_control_plane_001',
    'agentic_ai_control_plane',
    'AI Control Plane for Agentic Systems',
    'normal',
    $$
    {
      "executive_intuition": "A model answers. An agent acts. The moment an AI system can call tools, change records, trigger workflows, or influence business decisions, architecture must control runtime behavior. The control plane is that governance layer.",
      "plain_english": "Think of an AI application like a city. The model is not the whole city. The roads, traffic lights, police rules, emergency exits, licenses, cameras, and control rooms matter. In AI systems, these are policies, permissions, routing, logs, evaluations, fallback rules, and rollback mechanisms.",
      "step_by_step": [
        "First, define what the AI system is allowed to do.",
        "Second, define which tools, data, and actions require permission.",
        "Third, route requests to the right model, prompt, tool, or workflow.",
        "Fourth, evaluate outputs and actions before or after execution.",
        "Fifth, log decisions so failures can be traced.",
        "Sixth, provide fallback and rollback when behavior becomes unsafe or wrong."
      ],
      "concrete_example": "A procurement AI agent can summarize a supplier contract safely. But approving a purchase order is different. That action needs policy checks, financial threshold rules, audit logging, escalation, and possibly human approval.",
      "architecture_translation": "In architecture terms, the control plane sits above models and tools. It manages policy, permissions, routing, prompt versions, model selection, tool access, evaluation, observability, and rollback. The data plane performs the actual work: retrieval, generation, API calls, and workflow execution.",
      "common_mistakes": [
        "Treating the LLM as the whole system.",
        "Adding tools before defining permissions.",
        "Assuming human-in-the-loop solves everything.",
        "Changing prompts or policies without versioning.",
        "Not logging why the AI system took an action.",
        "Building demos that cannot be operated safely in production."
      ],
      "failure_mode": "A small prompt or routing change can silently alter behavior for a subset of users. Without versioning, evaluation, replay logs, and rollback, the team cannot prove what changed, who changed it, why it failed, or how to restore the last safe behavior.",
      "decision_checklist": [
        "What actions can the AI system take?",
        "Which actions need approval?",
        "Which tools can it call?",
        "Which data is it allowed to see?",
        "How are prompts and policies versioned?",
        "How are outputs evaluated?",
        "What gets logged?",
        "How do we rollback unsafe behavior?",
        "Who is accountable when the system acts?"
      ],
      "worked_scenario": "A client wants a manless AMS support agent. A weak architect says yes and builds a bot. A strong architect separates low-risk actions from high-risk actions. Password reset guidance, ticket classification, and knowledge retrieval may be zero-touch. Production changes, access updates, deletion, financial impact, and customer commitments require control-plane policies, audit, and approval."
    }
    $$::JSONB,
    $$
    [
      {
        "title": "NIST AI Risk Management Framework",
        "url": "https://www.nist.gov/itl/ai-risk-management-framework"
      },
      {
        "title": "OpenAI Platform Documentation",
        "url": "https://platform.openai.com/docs"
      }
    ]
    $$::JSONB,
    $$
    [
      {
        "title": "Study later: tool calling, evaluation, observability, rollback design",
        "url": "https://platform.openai.com/docs"
      }
    ]
    $$::JSONB,
    'published',
    1
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    lesson_type = EXCLUDED.lesson_type,
    content = EXCLUDED.content,
    source_links = EXCLUDED.source_links,
    deeper_reading = EXCLUDED.deeper_reading,
    status = EXCLUDED.status,
    version = EXCLUDED.version,
    updated_at = NOW();

INSERT INTO assessments (
    id,
    topic_id,
    lesson_id,
    title,
    pass_mcq_percent,
    descriptive_min_stars
)
VALUES (
    'asm_agentic_ai_control_plane_001',
    'agentic_ai_control_plane',
    'lesson_agentic_ai_control_plane_001',
    'Assessment: AI Control Plane for Agentic Systems',
    70,
    3
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    pass_mcq_percent = EXCLUDED.pass_mcq_percent,
    descriptive_min_stars = EXCLUDED.descriptive_min_stars;

DELETE FROM assessment_questions
WHERE assessment_id = 'asm_agentic_ai_control_plane_001';

INSERT INTO assessment_questions (
    id,
    assessment_id,
    question_type,
    question,
    options,
    correct_answer,
    explanation,
    is_critical,
    rubric,
    sort_order
)
VALUES
(
    'q_agentic_cp_001',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'What is the best definition of an AI control plane?',
    '{"A":"The neural network layer that trains the model","B":"The runtime governance layer that manages policies, permissions, routing, evaluation, audit, and rollback","C":"The database where embeddings are stored","D":"The UI layer where users chat with the AI"}'::JSONB,
    'B',
    'The control plane governs runtime behavior beyond the model itself.',
    TRUE,
    '{}'::JSONB,
    1
),
(
    'q_agentic_cp_002',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'Why should an AI architect care about the control plane?',
    '{"A":"Because it removes the need for data engineering","B":"Because production behavior is shaped by prompts, policies, tools, permissions, evaluators, and model routing","C":"Because it replaces cloud architecture","D":"Because it makes MCQ assessment easier"}'::JSONB,
    'B',
    'The lesson states that production behavior is not determined by the model alone.',
    FALSE,
    '{}'::JSONB,
    2
),
(
    'q_agentic_cp_003',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'Which item belongs more clearly to the data plane than the control plane?',
    '{"A":"Prompt version policy","B":"Approval rules for risky actions","C":"The actual API call or retrieval operation performed by the system","D":"Rollback rule for unsafe behavior"}'::JSONB,
    'C',
    'The data plane performs the actual work, while the control plane governs the work.',
    FALSE,
    '{}'::JSONB,
    3
),
(
    'q_agentic_cp_004',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'Which production practice is most dangerous?',
    '{"A":"Logging AI decisions","B":"Versioning prompts and policies","C":"Changing prompts, routing, or permissions without versioning, evaluation, replay, or rollback","D":"Separating low-risk and high-risk actions"}'::JSONB,
    'C',
    'Unversioned runtime changes create silent behavior drift and weak recovery.',
    TRUE,
    '{}'::JSONB,
    4
),
(
    'q_agentic_cp_005',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'What lower-level concepts help explain the control plane?',
    '{"A":"Prompts, context windows, tool calling, evaluators, and access control","B":"Only calculus and linear algebra","C":"Only frontend design","D":"Only GPU memory and training throughput"}'::JSONB,
    'A',
    'The topic glue connects control plane to prompts, tool calling, evaluators, and access control.',
    FALSE,
    '{}'::JSONB,
    5
),
(
    'q_agentic_cp_006',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'What is a common mistake with human-in-the-loop design?',
    '{"A":"Assuming human-in-the-loop automatically solves risk without defining escalation, permissions, and accountability","B":"Using humans for any approval","C":"Logging human approvals","D":"Separating high-risk and low-risk actions"}'::JSONB,
    'A',
    'Human review is not enough unless the architecture defines when, why, and how review works.',
    FALSE,
    '{}'::JSONB,
    6
),
(
    'q_agentic_cp_007',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'A procurement agent wants to approve a high-value purchase order. What should the architecture do?',
    '{"A":"Let the model decide if confidence is high","B":"Apply policy checks, permission checks, audit logging, threshold rules, and escalation or human approval","C":"Block all procurement use cases","D":"Send the request to a bigger model and trust the answer"}'::JSONB,
    'B',
    'High-impact actions need control-plane safeguards before execution.',
    TRUE,
    '{}'::JSONB,
    7
),
(
    'q_agentic_cp_008',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'What is the correct assessment principle for this platform?',
    '{"A":"Ask anything from AI because architects should know everything","B":"Use only tricky questions to expose weakness","C":"Evaluate concepts that were not taught to create challenge","D":"Assess only what the lesson actually explained"}'::JSONB,
    'D',
    'The platform must not evaluate concepts it did not teach.',
    FALSE,
    '{}'::JSONB,
    8
),
(
    'q_agentic_cp_009',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'Which failure mode best matches the lesson?',
    '{"A":"The UI color theme becomes inconsistent","B":"A small prompt or routing change silently alters behavior and the team cannot replay or rollback the cause","C":"The model trains too slowly","D":"The database has too many columns"}'::JSONB,
    'B',
    'Silent runtime behavior drift is a core production failure mode.',
    FALSE,
    '{}'::JSONB,
    9
),
(
    'q_agentic_cp_010',
    'asm_agentic_ai_control_plane_001',
    'mcq',
    'Why separate the control plane from the application UI?',
    '{"A":"To make the UI look simpler","B":"To govern behavior centrally through policy, permissions, routing, evaluation, logs, and rollback","C":"To avoid using databases","D":"To remove the need for architecture decisions"}'::JSONB,
    'B',
    'The control plane exists to centrally govern runtime behavior.',
    FALSE,
    '{}'::JSONB,
    10
),
(
    'dq_agentic_cp_001',
    'asm_agentic_ai_control_plane_001',
    'descriptive',
    'A client asks for a mostly autonomous procurement support agent. Explain the control-plane safeguards you would require before allowing the agent to take business-impacting actions.',
    NULL,
    NULL,
    'A strong answer separates low-risk and high-risk actions, defines permissions, approval thresholds, audit logging, evaluation, rollback, and accountability.',
    FALSE,
    '{"min_star_3":"Mentions policy checks, permissions, audit, and human approval for risky actions.","min_star_4":"Also separates data plane and control plane, explains failure modes, and defines rollback.","min_star_5":"Adds clear trade-offs, operating ownership, evaluation strategy, and production recovery logic."}'::JSONB,
    11
);

INSERT INTO resources (
    topic_id,
    title,
    url,
    resource_type,
    notes
)
VALUES
(
    'agentic_ai_control_plane',
    'NIST AI Risk Management Framework',
    'https://www.nist.gov/itl/ai-risk-management-framework',
    'official',
    'Useful for governance and risk vocabulary.'
),
(
    'agentic_ai_control_plane',
    'OpenAI Platform Documentation',
    'https://platform.openai.com/docs',
    'official',
    'Useful for implementation concepts around models, tools, and evaluation.'
)
ON CONFLICT DO NOTHING;
