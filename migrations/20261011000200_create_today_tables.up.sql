-- Ticked tasks of the study plan: one row per student and task.
CREATE TABLE task_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    plan_task_id INTEGER NOT NULL REFERENCES plan_tasks (id) ON DELETE CASCADE,
    checked_at TEXT NOT NULL,
    created_at TEXT, updated_at TEXT,
    UNIQUE (user_id, plan_task_id)
);
CREATE INDEX task_checks_plan_task_id ON task_checks (plan_task_id);

-- Study time per day and subject (a finished plan day is recorded here).
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    subject TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT, updated_at TEXT
);
CREATE INDEX study_sessions_user_date ON study_sessions (user_id, date);
