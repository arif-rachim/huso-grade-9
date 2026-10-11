use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;

/// A ticked plan task. Unique per student and task (the Plan tracker reuses it).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "task_checks")]
pub struct TaskCheck {
    pub id: i64,
    pub user_id: i64,
    pub plan_task_id: i64,
    pub checked_at: DateTime,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

/// Study time on a day (a finished plan day writes one).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "study_sessions")]
pub struct StudySession {
    pub id: i64,
    pub user_id: i64,
    pub date: NaiveDate,
    pub minutes: i64,
    pub subject: String,
    pub note: String,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}
