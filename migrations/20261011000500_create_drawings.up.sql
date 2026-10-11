-- "Redraw from memory": the student's drawing of a subtopic (a PNG from the canvas or a photo).
CREATE TABLE drawings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics (id) ON DELETE CASCADE,
    image_path TEXT NOT NULL,
    notes TEXT,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX drawings_user_id ON drawings (user_id);
CREATE INDEX drawings_topic_id ON drawings (topic_id);
