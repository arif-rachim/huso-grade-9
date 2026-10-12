use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;

pub const OPEN: &str = "open";
pub const RESOLVED: &str = "resolved";

pub const ORIGIN_ATTEMPT: &str = "attempt";
pub const ORIGIN_MANUAL: &str = "manual";

/// Why the mistake happened: `(value, label, hint)`.
pub const CAUSES: [(&str, &str, &str); 5] = [
    ("concept", "Concept", "I did not know or understand it"),
    (
        "calculation",
        "Calculation",
        "I knew it but slipped in the maths",
    ),
    ("misread", "Misread", "I read the question wrong"),
    ("rushed", "Rushed", "I went too fast"),
    ("guess", "Guess", "I guessed"),
];

pub fn cause_label(cause: &str) -> &'static str {
    CAUSES
        .iter()
        .find(|(value, _, _)| *value == cause)
        .map_or("Not set", |(_, label, _)| label)
}

pub fn is_cause(value: &str) -> bool {
    CAUSES.iter().any(|(v, _, _)| *v == value)
}

/// One mistake to learn from: a wrong or guessed answer, or a paper question added by hand.
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "error_entries")]
pub struct ErrorEntry {
    pub id: i64,
    pub user_id: i64,
    pub origin: String,
    pub answer_id: Option<i64>,
    pub question_id: Option<i64>,
    pub external_log_id: Option<i64>,
    pub topic_id: i64,
    /// Subject slug.
    pub subject: String,
    pub source: Option<String>,
    pub question_no: Option<String>,
    pub cause: Option<String>,
    pub note: Option<String>,
    /// Key of the sketch photo in private storage.
    pub photo: Option<String>,
    pub box_no: i64,
    pub due_on: NaiveDate,
    pub status: String,
    pub reviews: i64,
    pub last_grade: Option<String>,
    pub resolved_at: Option<DateTime>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl ErrorEntry {
    pub fn is_resolved(&self) -> bool {
        self.resolved_at.is_some()
    }

    pub fn has_cause(&self) -> bool {
        self.cause.as_deref().is_some_and(is_cause)
    }
}
