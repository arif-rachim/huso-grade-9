-- Spaced repetition (5-box Leitner). One state per student and card; an occlusion card has
-- one state per hidden label (`label` is the empty string for every other card type).
CREATE TABLE card_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    flashcard_id INTEGER NOT NULL REFERENCES flashcards (id) ON DELETE CASCADE,
    label TEXT NOT NULL DEFAULT '',
    box INTEGER NOT NULL DEFAULT 1,
    due_on TEXT NOT NULL,
    reviews INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    last_grade TEXT,
    -- The day the card was first reviewed: counts against the 20 new cards a day.
    introduced_on TEXT NOT NULL,
    created_at TEXT, updated_at TEXT,
    UNIQUE (user_id, flashcard_id, label)
);
CREATE INDEX card_states_due ON card_states (user_id, due_on);

CREATE TABLE card_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    flashcard_id INTEGER NOT NULL REFERENCES flashcards (id) ON DELETE CASCADE,
    label TEXT NOT NULL DEFAULT '',
    grade TEXT NOT NULL,
    reviewed_at TEXT NOT NULL,
    box_before INTEGER NOT NULL,
    box_after INTEGER NOT NULL,
    created_at TEXT, updated_at TEXT
);
CREATE INDEX card_reviews_user ON card_reviews (user_id, reviewed_at);
