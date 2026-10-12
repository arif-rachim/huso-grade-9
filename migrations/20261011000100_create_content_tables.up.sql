CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    color TEXT NOT NULL,
    emoji TEXT NOT NULL,
    level_hint TEXT,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT, updated_at TEXT
);

CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    subject_id INTEGER NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES topics (id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    items TEXT NOT NULL DEFAULT '[]',
    position INTEGER NOT NULL DEFAULT 0,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX topics_subject_id ON topics (subject_id);
CREATE INDEX topics_parent_id ON topics (parent_id);

CREATE TABLE plan_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    phase TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    subject TEXT NOT NULL,
    title TEXT NOT NULL,
    issue INTEGER,
    new_subtopics TEXT NOT NULL DEFAULT '[]',
    created_at TEXT, updated_at TEXT
);

CREATE TABLE plan_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_day_id INTEGER NOT NULL REFERENCES plan_days (id) ON DELETE CASCADE,
    block_label TEXT NOT NULL,
    block_minutes INTEGER NOT NULL,
    block_subtopics TEXT NOT NULL DEFAULT '[]',
    label TEXT NOT NULL,
    position INTEGER NOT NULL,
    created_at TEXT, updated_at TEXT,
    UNIQUE (plan_day_id, position)
);

CREATE TABLE flashcards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    topic_id INTEGER NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    card_type TEXT NOT NULL,
    front TEXT NOT NULL DEFAULT '',
    back TEXT NOT NULL DEFAULT '',
    visual TEXT,
    sketch_prompt TEXT,
    payload TEXT NOT NULL DEFAULT '{}',
    tags TEXT NOT NULL DEFAULT '[]',
    origin TEXT NOT NULL DEFAULT 'content',
    archived_at TEXT,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX flashcards_topic_id ON flashcards (topic_id);

CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    topic_id INTEGER NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    difficulty INTEGER NOT NULL,
    stem TEXT NOT NULL,
    visual TEXT,
    choice_a TEXT NOT NULL,
    choice_b TEXT NOT NULL,
    choice_c TEXT NOT NULL,
    choice_d TEXT NOT NULL,
    choice_e TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    explanation_visual TEXT,
    source TEXT NOT NULL DEFAULT 'original',
    archived_at TEXT,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX questions_topic_id ON questions (topic_id);
