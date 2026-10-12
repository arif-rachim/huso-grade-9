use crate::app::practice::scoring::Tally;
use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;

/// The 2024 HUSO pack: the diagnostic test of 12 October.
pub const DIAGNOSTIC_SOURCE: &str = "huso-2024-r1";

/// Practice done outside the app: one row per subject.
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "external_logs")]
pub struct ExternalLog {
    pub id: i64,
    pub user_id: i64,
    pub date: NaiveDate,
    pub source: String,
    pub subject: String,
    pub topic_id: Option<i64>,
    pub correct: i64,
    pub wrong: i64,
    pub blank: i64,
    pub minutes: i64,
    pub note: String,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl ExternalLog {
    pub fn tally(&self) -> Tally {
        Tally {
            correct: self.correct,
            wrong: self.wrong,
            blank: self.blank,
        }
    }
}
