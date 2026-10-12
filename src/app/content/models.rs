use super::lesson_file::WatchLink;
use renox::chrono::NaiveDate;
use renox::db::Json;
use renox::prelude::*;
use serde::Serialize;

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "subjects")]
pub struct Subject {
    pub id: i64,
    pub slug: String,
    pub name: String,
    pub color: String,
    pub emoji: String,
    pub level_hint: Option<String>,
    pub position: i64,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

/// A topic (`parent_id` is null) or a subtopic (`parent_id` is its topic).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "topics")]
pub struct Topic {
    pub id: i64,
    pub slug: String,
    pub subject_id: i64,
    pub parent_id: Option<i64>,
    pub name: String,
    pub items: Json<Vec<String>>,
    pub position: i64,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "plan_days")]
pub struct PlanDay {
    pub id: i64,
    pub date: NaiveDate,
    pub phase: String,
    pub minutes: i64,
    pub subject: String,
    pub title: String,
    pub issue: Option<i64>,
    pub new_subtopics: Json<Vec<String>>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "plan_tasks")]
pub struct PlanTask {
    pub id: i64,
    pub plan_day_id: i64,
    pub block_label: String,
    pub block_minutes: i64,
    pub block_subtopics: Json<Vec<String>>,
    pub label: String,
    pub position: i64,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "flashcards")]
pub struct Flashcard {
    pub id: i64,
    pub key: String,
    pub topic_id: i64,
    pub card_type: String,
    pub front: String,
    pub back: String,
    pub visual: Option<String>,
    pub sketch_prompt: Option<String>,
    pub payload: Json<renox::serde_json::Value>,
    pub tags: Json<Vec<String>>,
    /// `content` (from the JSON files) or `manual` (made by the student or parent).
    pub origin: String,
    pub archived_at: Option<DateTime>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "questions")]
pub struct Question {
    pub id: i64,
    pub key: String,
    pub topic_id: i64,
    pub difficulty: i64,
    pub stem: String,
    pub visual: Option<String>,
    pub choice_a: String,
    pub choice_b: String,
    pub choice_c: String,
    pub choice_d: String,
    pub choice_e: String,
    pub answer: String,
    pub explanation: String,
    pub explanation_visual: Option<String>,
    pub source: String,
    pub archived_at: Option<DateTime>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl Question {
    /// The five choices as `(letter, text)`.
    pub fn choices(&self) -> [(&'static str, &str); 5] {
        [
            ("A", &self.choice_a),
            ("B", &self.choice_b),
            ("C", &self.choice_c),
            ("D", &self.choice_d),
            ("E", &self.choice_e),
        ]
    }
}

/// The visual lesson of a subtopic (from `materi/<subject>/*.md`).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "lessons")]
pub struct Lesson {
    pub id: i64,
    pub topic_id: i64,
    pub title: String,
    pub markdown: String,
    pub watch_links: Json<Vec<WatchLink>>,
    /// The file it was imported from.
    pub source_path: String,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}
