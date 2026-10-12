-- The visual lesson of a subtopic, imported from materi/<subject>/*.md.
CREATE TABLE lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL UNIQUE REFERENCES topics (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    markdown TEXT NOT NULL,
    watch_links TEXT NOT NULL DEFAULT '[]',
    source_path TEXT NOT NULL DEFAULT '',
    created_at TEXT, updated_at TEXT
);

-- What the student did on a lesson: a "redrew it from memory" mark (score NULL) or a try of
-- "Check your understanding" (score 0-5 and the chosen letters). `drawn` is kept equal on all
-- the rows of one student and topic.
CREATE TABLE lesson_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    score INTEGER CHECK (score IS NULL OR (score >= 0 AND score <= 5)),
    drawn INTEGER NOT NULL DEFAULT 0,
    answers TEXT NOT NULL DEFAULT '{}',
    checked_on TEXT NOT NULL,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX lesson_checks_user_topic ON lesson_checks (user_id, topic_id);
