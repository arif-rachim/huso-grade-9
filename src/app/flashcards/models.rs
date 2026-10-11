use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;

/// Where one card (one label of an occlusion card) is in the Leitner boxes for one student.
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "card_states")]
pub struct CardState {
    pub id: i64,
    pub user_id: i64,
    pub flashcard_id: i64,
    /// The hidden label of an occlusion card; empty for every other card.
    pub label: String,
    pub r#box: i64,
    pub due_on: NaiveDate,
    pub reviews: i64,
    pub lapses: i64,
    pub last_grade: Option<String>,
    pub introduced_on: NaiveDate,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

/// One answer the student gave while reviewing.
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "card_reviews")]
pub struct CardReview {
    pub id: i64,
    pub user_id: i64,
    pub flashcard_id: i64,
    pub label: String,
    pub grade: String,
    pub reviewed_at: DateTime,
    pub box_before: i64,
    pub box_after: i64,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}
