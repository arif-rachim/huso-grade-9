CREATE TABLE error_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    -- attempt | manual
    origin TEXT NOT NULL DEFAULT 'attempt',
    answer_id INTEGER REFERENCES answers (id) ON DELETE SET NULL,
    -- The bank question to redo (null for a paper question).
    question_id INTEGER REFERENCES questions (id) ON DELETE SET NULL,
    -- Reserved for the progress log (external_logs does not exist yet): no foreign key.
    external_log_id INTEGER,
    topic_id INTEGER NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    -- The subject slug, kept here so the list can filter on it.
    subject TEXT NOT NULL,
    -- Manual entries: where the question is from (a source title or free text) and its number.
    source TEXT,
    question_no TEXT,
    -- concept | calculation | misread | rushed | guess; null until chosen.
    cause TEXT,
    note TEXT,
    -- Key of the sketch photo in private storage (errors/<random>.jpg).
    photo TEXT,
    box_no INTEGER NOT NULL DEFAULT 1,
    due_on TEXT NOT NULL,
    -- open | resolved (kept in step with resolved_at so the list can filter on it)
    status TEXT NOT NULL DEFAULT 'open',
    reviews INTEGER NOT NULL DEFAULT 0,
    last_grade TEXT,
    resolved_at TEXT,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX error_entries_user_due ON error_entries (user_id, status, due_on);
CREATE INDEX error_entries_question ON error_entries (user_id, question_id);
CREATE INDEX error_entries_answer ON error_entries (answer_id);
