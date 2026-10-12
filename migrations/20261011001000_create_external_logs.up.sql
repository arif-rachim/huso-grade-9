-- Practice done outside the app (paper tests, AMC, Physics Bowl, ...): one row per subject.
CREATE TABLE external_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    -- A past paper slug (huso-2024-r1), a practice source title or free text.
    source TEXT NOT NULL,
    -- Subject slug (math, physics, ...).
    subject TEXT NOT NULL,
    topic_id INTEGER REFERENCES topics (id) ON DELETE SET NULL,
    correct INTEGER NOT NULL DEFAULT 0,
    wrong INTEGER NOT NULL DEFAULT 0,
    blank INTEGER NOT NULL DEFAULT 0,
    minutes INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT, updated_at TEXT
);
CREATE INDEX external_logs_user_date ON external_logs (user_id, date);
