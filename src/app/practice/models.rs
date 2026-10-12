use renox::chrono::Duration;
use renox::db::Json;
use renox::prelude::*;
use serde::{Deserialize, Serialize};

pub const TOPIC: &str = "topic";
pub const SPRINT: &str = "sprint";
pub const MIXED: &str = "mixed";
pub const SIMULATION: &str = "simulation";
/// Redo the questions of the Error Log that are due.
pub const ERRORS: &str = "errors";

/// One section of a Round 1 simulation: a subject with its own 36-minute timer.
#[derive(Serialize, Deserialize, Default, Debug, Clone, PartialEq, Eq)]
pub struct Section {
    pub subject: String,
    pub name: String,
    /// Position (0-based) of the section's first question in `Attempt::question_ids`.
    pub start: i64,
    pub count: i64,
    pub secs: i64,
}

/// One practice run. The questions are drawn once, when it starts, and kept in
/// `question_ids` so that a refresh shows the same ones.
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "attempts")]
pub struct Attempt {
    pub id: i64,
    pub user_id: i64,
    pub mode: String,
    pub subject: Option<String>,
    pub topic_id: Option<i64>,
    pub started_at: DateTime,
    pub finished_at: Option<DateTime>,
    pub time_limit_secs: Option<i64>,
    pub question_ids: Json<Vec<i64>>,
    pub sections: Json<Vec<Section>>,
    pub section: i64,
    pub section_started_at: Option<DateTime>,
    pub last_activity_at: Option<DateTime>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl Attempt {
    pub fn is_finished(&self) -> bool {
        self.finished_at.is_some()
    }

    pub fn is_simulation(&self) -> bool {
        self.mode == SIMULATION
    }

    /// Explanations appear right after each answer only in topic mode.
    pub fn explains_at_once(&self) -> bool {
        self.mode == TOPIC
    }

    pub fn len(&self) -> i64 {
        self.question_ids.len() as i64
    }

    pub fn is_empty(&self) -> bool {
        self.question_ids.is_empty()
    }

    /// The running section, if this is a simulation.
    pub fn current_section(&self) -> Option<&Section> {
        if self.is_simulation() {
            self.sections.get(self.section as usize)
        } else {
            None
        }
    }

    /// `(first position, number of positions)` the student may answer now.
    pub fn open_range(&self) -> (i64, i64) {
        match self.current_section() {
            Some(s) => (s.start, s.count),
            None => (0, self.len()),
        }
    }

    pub fn is_open(&self, position: i64) -> bool {
        let (start, count) = self.open_range();
        !self.is_finished() && position >= start && position < start + count
    }

    /// When the running timer ends (the section's, or the whole attempt's), if there is one.
    pub fn deadline(&self) -> Option<DateTime> {
        if self.is_finished() {
            return None;
        }
        if let Some(section) = self.current_section() {
            return self
                .section_started_at
                .map(|at| at + Duration::seconds(section.secs));
        }
        self.time_limit_secs
            .map(|secs| self.started_at + Duration::seconds(secs))
    }

    /// Seconds left on the running timer (never negative), or none without a timer.
    pub fn remaining_secs(&self, now: DateTime) -> Option<i64> {
        self.deadline().map(|d| (d - now).num_seconds().max(0))
    }
}

/// One question of an attempt. A row exists for every question from the start; `answered_at`
/// is null until the student answered or skipped it, or the section/attempt was closed.
///
/// The Error Log reads the rows of finished attempts where
/// `is_correct = false OR guessed = true` (see `scoring::is_wrong_or_guessed`).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "answers")]
pub struct Answer {
    pub id: i64,
    pub attempt_id: i64,
    pub question_id: i64,
    pub position: i64,
    /// `A`..`E`, or none for a blank.
    pub choice: Option<String>,
    pub is_correct: bool,
    pub guessed: bool,
    pub seconds: i64,
    pub answered_at: Option<DateTime>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl Answer {
    pub fn is_blank(&self) -> bool {
        self.choice.is_none()
    }

    /// Wrong, blank or marked as a guess: this one belongs in the Error Log.
    pub fn needs_review(&self) -> bool {
        super::scoring::is_wrong_or_guessed(self.is_correct, self.guessed)
    }
}
