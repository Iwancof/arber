-- 04_ops_chat_extension.sql
-- Addendum schema for Operations Chat Copilot
-- Compatible with ledger-separated Event Intelligence OS design.

CREATE SCHEMA IF NOT EXISTS ops_chat;

CREATE TABLE IF NOT EXISTS ops_chat.chat_session (
    session_id UUID PRIMARY KEY,
    channel TEXT NOT NULL DEFAULT 'claude_code',
    actor_user_id TEXT NOT NULL,
    actor_display_name TEXT,
    session_mode TEXT NOT NULL CHECK (session_mode IN ('observe','advise','operate','implement')),
    title TEXT,
    active_scope_type TEXT,
    active_scope_key TEXT,
    trace_id TEXT NOT NULL,
    correlation_id TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','paused','closed'))
);

CREATE INDEX IF NOT EXISTS ix_chat_session_actor ON ops_chat.chat_session(actor_user_id, status, last_activity_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.chat_message (
    message_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ops_chat.chat_session(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('system','user','assistant','tool')),
    content_md TEXT NOT NULL,
    content_json JSONB,
    provenance_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_message_session ON ops_chat.chat_message(session_id, created_at);

CREATE TABLE IF NOT EXISTS ops_chat.context_capsule (
    capsule_id UUID PRIMARY KEY,
    capsule_type TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fresh_until TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'fresh' CHECK (status IN ('fresh','stale','degraded','failed')),
    summary_md TEXT NOT NULL,
    summary_json JSONB NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_id TEXT NOT NULL,
    created_by TEXT NOT NULL DEFAULT 'capsule_assembler'
);

CREATE INDEX IF NOT EXISTS ix_context_capsule_lookup
    ON ops_chat.context_capsule(capsule_type, scope_key, generated_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.context_capsule_source_ref (
    capsule_id UUID NOT NULL REFERENCES ops_chat.context_capsule(capsule_id) ON DELETE CASCADE,
    ref_kind TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    PRIMARY KEY (capsule_id, ref_kind, ref_id)
);

CREATE TABLE IF NOT EXISTS ops_chat.chat_intent (
    intent_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ops_chat.chat_session(session_id) ON DELETE CASCADE,
    source_message_id UUID NOT NULL REFERENCES ops_chat.chat_message(message_id) ON DELETE CASCADE,
    intent_type TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    intent_json JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'parsed' CHECK (status IN ('parsed','draft','proposed','executed','rejected','failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_intent_session ON ops_chat.chat_intent(session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.chat_action_proposal (
    proposal_id UUID PRIMARY KEY,
    intent_id UUID NOT NULL REFERENCES ops_chat.chat_intent(intent_id) ON DELETE CASCADE,
    proposal_type TEXT NOT NULL,
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('low','medium','high','critical')),
    requires_confirmation BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    summary_md TEXT NOT NULL,
    diff_json JSONB,
    command_json JSONB NOT NULL,
    blocked_by JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','rejected','executed','expired','failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ,
    confirmed_by TEXT
);

CREATE INDEX IF NOT EXISTS ix_chat_action_proposal_status ON ops_chat.chat_action_proposal(status, created_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.chat_action_execution (
    execution_id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES ops_chat.chat_action_proposal(proposal_id) ON DELETE CASCADE,
    executed_by TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    result_status TEXT NOT NULL CHECK (result_status IN ('success','partial','failed','rejected')),
    result_json JSONB NOT NULL,
    linked_event_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    trace_id TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_action_execution_proposal ON ops_chat.chat_action_execution(proposal_id, executed_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.chat_memory_note (
    note_id UUID PRIMARY KEY,
    scope_type TEXT NOT NULL,
    scope_key TEXT NOT NULL,
    note_type TEXT NOT NULL,
    source_session_id UUID REFERENCES ops_chat.chat_session(session_id) ON DELETE SET NULL,
    source_message_id UUID REFERENCES ops_chat.chat_message(message_id) ON DELETE SET NULL,
    body_md TEXT NOT NULL,
    body_json JSONB,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','superseded','archived')),
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_memory_note_scope ON ops_chat.chat_memory_note(scope_type, scope_key, created_at DESC);

CREATE TABLE IF NOT EXISTS ops_chat.chat_mode_transition (
    transition_id UUID PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ops_chat.chat_session(session_id) ON DELETE CASCADE,
    from_mode TEXT NOT NULL,
    to_mode TEXT NOT NULL,
    approved_by TEXT,
    reason_md TEXT,
    approved_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    trace_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_mode_transition_session ON ops_chat.chat_mode_transition(session_id, created_at DESC);

-- Suggested outbox topics (logical only; actual outbox table may already exist)
-- ops_chat.context_capsule.created
-- ops_chat.intent.parsed
-- ops_chat.proposal.created
-- ops_chat.proposal.confirmed
-- ops_chat.execution.completed
-- ops_chat.note.created
