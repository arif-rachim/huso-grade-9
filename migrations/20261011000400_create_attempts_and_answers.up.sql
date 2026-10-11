CREATE TABLE attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    -- topic, sprint, mixed, simulation (errors: reserved for the Error Log feature)
    mode TEXT NOT NULL,
    subject TEXT,
    topic_id INTEGER REFERENCES topics (id) ON DELETE SET NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    -- Whole-attempt limit in seconds (sprint, mixed); null = no timer or per-section timers.
    time_limit_secs INTEGER,
    -- The questions in the order they were drawn (JSON array of question ids): a refresh keeps them.
    question_ids TEXT NOT NULL DEFAULT '[]',
    -- Simulation only: JSON array of {subject, name, start, count, secs}; [] for other modes.
    sections TEXT NOT NULL DEFAULT '[]',
    -- Simulation only: the running section (0-based) and when it started.
    section INTEGER NOT NULL DEFAULT 0,
    section_started_at TEXT,
    -- When the student last saved an answer: the time since then is the next answer's `seconds`.
    last_activity_at TEXT,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX attempts_user_id ON attempts (user_id);

CREATE TABLE answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts (id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    -- 0-based place in attempts.question_ids; one row per question is made when the attempt starts.
    position INTEGER NOT NULL,
    -- 'A'..'E'; null = blank (skipped, or time ran out)
    choice TEXT,
    is_correct INTEGER NOT NULL DEFAULT 0,
    guessed INTEGER NOT NULL DEFAULT 0,
    seconds INTEGER NOT NULL DEFAULT 0,
    -- null until the student answered or skipped it, or the attempt/section was closed.
    answered_at TEXT,
    created_at TEXT, updated_at TEXT,
    UNIQUE (attempt_id, position)
);
CREATE INDEX answers_question_id ON answers (question_id);
