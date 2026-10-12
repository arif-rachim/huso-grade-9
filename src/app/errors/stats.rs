//! Numbers for the Error Log page: the cause pie, the Top 10 subtopics, what is due.

use super::models::{ErrorEntry, OPEN};
use crate::app::content::models::{Subject, Topic};
use renox::chrono::NaiveDate;
use renox::prelude::*;
use std::collections::HashMap;

/// Mistakes per cause (every entry of the student, open or resolved), biggest first; entries
/// without a cause are counted as `none`.
pub async fn cause_counts(db: &Db, user_id: i64) -> Result<Vec<(String, i64)>> {
    let rows: Vec<(String, i64)> = renox::db::sql(
        "SELECT COALESCE(cause, 'none'), COUNT(*) AS n FROM error_entries \
         WHERE user_id = ? GROUP BY COALESCE(cause, 'none') ORDER BY n DESC, 1",
    )
    .bind(user_id)
    .fetch_as(db)
    .await?;
    Ok(rows)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TopSubtopic {
    pub slug: String,
    pub name: String,
    pub subject_name: String,
    pub color: String,
    pub count: i64,
}

/// The subtopics with the most entries (the "top mistakes" wall chart).
pub async fn top_subtopics(db: &Db, user_id: i64, limit: i64) -> Result<Vec<TopSubtopic>> {
    let rows: Vec<(i64, i64)> = renox::db::sql(
        "SELECT topic_id, COUNT(*) AS n FROM error_entries WHERE user_id = ? \
         GROUP BY topic_id ORDER BY n DESC, topic_id LIMIT ?",
    )
    .bind(user_id)
    .bind(limit)
    .fetch_as(db)
    .await?;
    let topics: HashMap<i64, Topic> = Topic::find_many(db, rows.iter().map(|(id, _)| *id))
        .await?
        .into_iter()
        .map(|t| (t.id, t))
        .collect();
    let subjects: HashMap<i64, Subject> =
        Subject::find_many(db, topics.values().map(|t| t.subject_id))
            .await?
            .into_iter()
            .map(|s| (s.id, s))
            .collect();
    Ok(rows
        .into_iter()
        .filter_map(|(topic_id, count)| {
            let topic = topics.get(&topic_id)?;
            let subject = subjects.get(&topic.subject_id)?;
            Some(TopSubtopic {
                slug: topic.slug.clone(),
                name: topic.name.clone(),
                subject_name: subject.name.clone(),
                color: subject.color.clone(),
                count,
            })
        })
        .collect())
}

/// Open entries due on `today` or earlier, oldest first.
pub async fn due_entries(db: &Db, user_id: i64, today: NaiveDate) -> Result<Vec<ErrorEntry>> {
    ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(user_id))
        .where_(ErrorEntry::STATUS.eq(OPEN))
        .where_(ErrorEntry::DUE_ON.lte(today))
        .order_by(ErrorEntry::DUE_ON)
        .order_by(ErrorEntry::ID)
        .get(db)
        .await
}

pub async fn due_count(db: &Db, user_id: i64, today: NaiveDate) -> Result<i64> {
    Ok(ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(user_id))
        .where_(ErrorEntry::STATUS.eq(OPEN))
        .where_(ErrorEntry::DUE_ON.lte(today))
        .count(db)
        .await? as i64)
}

/// Due open entries that come from the question bank (the "redo" practice can ask them again).
pub async fn redo_count(db: &Db, user_id: i64, today: NaiveDate) -> Result<i64> {
    Ok(ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(user_id))
        .where_(ErrorEntry::STATUS.eq(OPEN))
        .where_(ErrorEntry::DUE_ON.lte(today))
        .where_(ErrorEntry::QUESTION_ID.is_not_null())
        .count(db)
        .await? as i64)
}

/// The next day something is due, when nothing is due today.
pub async fn next_due(db: &Db, user_id: i64) -> Result<Option<NaiveDate>> {
    let first = ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(user_id))
        .where_(ErrorEntry::STATUS.eq(OPEN))
        .order_by(ErrorEntry::DUE_ON)
        .first(db)
        .await?;
    Ok(first.map(|e| e.due_on))
}

/// Question ids of the due open entries that come from the bank, oldest first (for the redo practice).
pub async fn due_question_ids(
    db: &Db,
    user_id: i64,
    today: NaiveDate,
    limit: u64,
) -> Result<Vec<i64>> {
    let entries = ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(user_id))
        .where_(ErrorEntry::STATUS.eq(OPEN))
        .where_(ErrorEntry::DUE_ON.lte(today))
        .where_(ErrorEntry::QUESTION_ID.is_not_null())
        .order_by(ErrorEntry::DUE_ON)
        .order_by(ErrorEntry::ID)
        .limit(limit)
        .get(db)
        .await?;
    let mut ids: Vec<i64> = Vec::new();
    for id in entries.into_iter().filter_map(|e| e.question_id) {
        if !ids.contains(&id) {
            ids.push(id);
        }
    }
    Ok(ids)
}
