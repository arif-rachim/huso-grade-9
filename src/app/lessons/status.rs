//! The READY status of a subtopic, and the lists built from it (Today's red list, the index).
//!
//! A subtopic is READY when the student has **drawn** it from memory, scored **at least 4 of 5**
//! on "Check your understanding", and still **remembers** it: its flashcards are in Leitner box 3
//! or higher, or its mastery is 70 or more. `status` is a pure function; the queries below only
//! gather its inputs.

use crate::app::content::models::{Lesson, PlanDay, Topic};
use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;
use std::collections::{HashMap, HashSet};

/// Best score needed on the check.
pub const PASS_SCORE: i64 = 4;
/// Leitner box from which a card counts as remembered.
pub const REMEMBERED_BOX: i64 = 3;
/// Mastery (0-100) from which a subtopic counts as remembered.
pub const REMEMBERED_MASTERY: i64 = 70;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Ready,
    InProgress,
    NotYet,
}

impl Status {
    pub fn label(self) -> &'static str {
        match self {
            Status::Ready => "READY",
            Status::InProgress => "In progress",
            Status::NotYet => "Not yet",
        }
    }

    pub fn icon(self) -> &'static str {
        match self {
            Status::Ready => "✅",
            Status::InProgress => "🟡",
            Status::NotYet => "🔴",
        }
    }

    /// The `rx-badge` kind.
    pub fn kind(self) -> &'static str {
        match self {
            Status::Ready => "success",
            Status::InProgress => "warning",
            Status::NotYet => "error",
        }
    }
}

/// Is the subtopic still remembered (cards in box 3+ or mastery 70+)?
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Retention {
    /// Flashcards and practice are not installed yet: this condition is not asked.
    NotTracked,
    Met,
    NotMet,
}

/// The READY rule. Pure, so it is easy to test.
///
/// * READY: drawn, best score >= 4, and the retention is met (or not tracked yet).
/// * Not yet: nothing done at all (not drawn, never checked).
/// * In progress: anything in between.
pub fn status(drawn: bool, best_score: Option<i64>, retention: Retention) -> Status {
    let passed = best_score.is_some_and(|s| s >= PASS_SCORE);
    if drawn && passed && retention != Retention::NotMet {
        Status::Ready
    } else if !drawn && best_score.is_none() {
        Status::NotYet
    } else {
        Status::InProgress
    }
}

/// What a student did on one subtopic, and the status that follows.
#[derive(Debug, Clone, Copy, Serialize)]
pub struct TopicState {
    pub drawn: bool,
    pub best_score: Option<i64>,
    pub status: Status,
}

impl TopicState {
    pub const NONE: TopicState = TopicState {
        drawn: false,
        best_score: None,
        status: Status::NotYet,
    };
}

async fn table_exists(db: &Db, name: &str) -> Result<bool> {
    let n: i64 =
        renox::db::sql("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?")
            .bind(name)
            .scalar(db)
            .await?;
    Ok(n > 0)
}

/// INTEGRATION POINT (Flashcards #19 and Practice / Syllabus map #28): which subtopics the
/// student still remembers. `None` while neither feature has its tables, so READY then depends
/// only on drawing and the check. Once they exist:
///
/// * cards: a subtopic is remembered when it has cards and all of them are in box >= 3
///   (`card_states.box`, per the spec in docs/PROJECT.md);
/// * mastery: replace `mastery_by_topic` with the real mastery calculation (0-100 per topic);
///   a mastery of 70 or more also counts.
async fn remembered_topics(db: &Db, user_id: i64) -> Result<Option<HashSet<i64>>> {
    let has_cards = table_exists(db, "card_states").await?;
    let mastery = mastery_by_topic(db, user_id).await?;
    if !has_cards && mastery.is_none() {
        return Ok(None);
    }
    let mut remembered = HashSet::new();
    if has_cards {
        let rows: Vec<(i64, i64, i64)> = renox::db::sql(
            "SELECT f.topic_id, COUNT(*), \
                    SUM(CASE WHEN COALESCE(cs.box, 0) >= ? THEN 1 ELSE 0 END) \
             FROM flashcards f \
             LEFT JOIN card_states cs ON cs.flashcard_id = f.id AND cs.user_id = ? \
             WHERE f.archived_at IS NULL GROUP BY f.topic_id",
        )
        .bind(REMEMBERED_BOX)
        .bind(user_id)
        .fetch_as::<(i64, i64, i64)>(db)
        .await?;
        for (topic_id, total, in_box) in rows {
            if total > 0 && in_box == total {
                remembered.insert(topic_id);
            }
        }
    }
    for (topic_id, value) in mastery.unwrap_or_default() {
        if value >= REMEMBERED_MASTERY {
            remembered.insert(topic_id);
        }
    }
    Ok(Some(remembered))
}

/// INTEGRATION POINT (#28): mastery 0-100 per topic id for the student, `None` until the
/// practice tables (`attempts`, `answers`) and the mastery calculation exist.
async fn mastery_by_topic(_db: &Db, _user_id: i64) -> Result<Option<HashMap<i64, i64>>> {
    Ok(None)
}

/// The state of every subtopic the student has touched; a missing topic is `TopicState::NONE`.
pub async fn states(db: &Db, user_id: i64) -> Result<HashMap<i64, TopicState>> {
    let rows: Vec<(i64, Option<i64>, i64)> = renox::db::sql(
        "SELECT topic_id, MAX(score), MAX(drawn) FROM lesson_checks WHERE user_id = ? \
         GROUP BY topic_id",
    )
    .bind(user_id)
    .fetch_as::<(i64, Option<i64>, i64)>(db)
    .await?;
    let mut raw: HashMap<i64, (bool, Option<i64>)> = rows
        .into_iter()
        .map(|(topic, best, drawn)| (topic, (drawn > 0, best)))
        .collect();
    // A saved drawing from the "Redraw from memory" page counts as drawn too.
    if table_exists(db, "drawings").await? {
        let drawn: Vec<i64> =
            renox::db::sql("SELECT DISTINCT topic_id FROM drawings WHERE user_id = ?")
                .bind(user_id)
                .scalars(db)
                .await?;
        for topic in drawn {
            raw.entry(topic).or_insert((false, None)).0 = true;
        }
    }
    let remembered = remembered_topics(db, user_id).await?;
    Ok(raw
        .into_iter()
        .map(|(topic, (drawn, best))| {
            let retention = match &remembered {
                None => Retention::NotTracked,
                Some(set) if set.contains(&topic) => Retention::Met,
                Some(_) => Retention::NotMet,
            };
            (
                topic,
                TopicState {
                    drawn,
                    best_score: best,
                    status: status(drawn, best, retention),
                },
            )
        })
        .collect())
}

/// The date each subtopic is first scheduled as new material (`plan_days.new_subtopics`).
pub async fn scheduled_dates(db: &Db) -> Result<HashMap<String, NaiveDate>> {
    let days = PlanDay::query().order_by(PlanDay::DATE).get(db).await?;
    let mut out = HashMap::new();
    for day in days {
        for slug in day.new_subtopics.0 {
            out.entry(slug).or_insert(day.date);
        }
    }
    Ok(out)
}

/// A subtopic on the red list.
#[derive(Debug, Clone, Serialize)]
pub struct RedItem {
    pub slug: String,
    pub name: String,
    pub color: String,
    pub subject: String,
    pub scheduled: String,
    pub status: Status,
    pub status_label: &'static str,
    pub status_icon: &'static str,
}

/// Which red list a date shows, if any: Sundays and 14 Nov list every subject; 9-13 Nov list the
/// subject of that day's remedial slot (`day_subject`). `None` for other days (and exam day).
pub fn red_list_scope(date: NaiveDate, day_subject: Option<&str>) -> Option<RedScope> {
    use renox::chrono::Datelike;
    let exam = crate::clock::exam_date();
    if date >= exam {
        return None;
    }
    let remedial_start = NaiveDate::from_ymd_opt(2026, 11, 9)?;
    let remedial_end = NaiveDate::from_ymd_opt(2026, 11, 13)?;
    if date >= remedial_start && date <= remedial_end {
        return match day_subject {
            Some(s) if crate::app::content::files::SUBJECTS.contains(&s) => {
                Some(RedScope::Subject(s.to_owned()))
            }
            _ => Some(RedScope::All),
        };
    }
    if date.weekday() == renox::chrono::Weekday::Sun || date == exam.pred_opt()? {
        return Some(RedScope::All);
    }
    None
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RedScope {
    All,
    Subject(String),
}

/// Subtopics with a lesson whose scheduled day is before `today` and that are not READY yet,
/// in schedule order.
pub async fn red_list(
    db: &Db,
    user_id: i64,
    today: NaiveDate,
    scope: &RedScope,
) -> Result<Vec<RedItem>> {
    let scheduled = scheduled_dates(db).await?;
    let states = states(db, user_id).await?;
    let lessons = Lesson::query().get(db).await?;
    let topic_ids: Vec<i64> = lessons.iter().map(|l| l.topic_id).collect();
    let topics = Topic::query()
        .where_(Topic::ID.is_in(topic_ids))
        .get(db)
        .await?;
    let subjects = crate::app::content::models::Subject::query()
        .get(db)
        .await?;
    let mut items = Vec::new();
    for topic in topics {
        let Some(date) = scheduled.get(&topic.slug).copied().filter(|d| *d < today) else {
            continue;
        };
        let Some(subject) = subjects.iter().find(|s| s.id == topic.subject_id) else {
            continue;
        };
        if let RedScope::Subject(slug) = scope
            && *slug != subject.slug
        {
            continue;
        }
        let state = states.get(&topic.id).copied().unwrap_or(TopicState::NONE);
        if state.status == Status::Ready {
            continue;
        }
        items.push((
            date,
            RedItem {
                slug: topic.slug,
                name: topic.name,
                color: subject.color.clone(),
                subject: subject.name.clone(),
                scheduled: date.format("%a %-d %b").to_string(),
                status: state.status,
                status_label: state.status.label(),
                status_icon: state.status.icon(),
            },
        ));
    }
    items.sort_by(|a, b| a.0.cmp(&b.0).then_with(|| a.1.slug.cmp(&b.1.slug)));
    Ok(items.into_iter().map(|(_, i)| i).collect())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ready_needs_drawing_a_good_score_and_retention() {
        use Retention::*;
        assert_eq!(status(true, Some(4), Met), Status::Ready);
        assert_eq!(status(true, Some(5), NotTracked), Status::Ready);
        assert_eq!(status(true, Some(3), Met), Status::InProgress);
        assert_eq!(status(false, Some(5), Met), Status::InProgress);
        assert_eq!(status(true, None, Met), Status::InProgress);
        assert_eq!(status(true, Some(5), NotMet), Status::InProgress);
        assert_eq!(status(false, None, NotTracked), Status::NotYet);
        assert_eq!(status(false, Some(1), NotTracked), Status::InProgress);
    }

    #[test]
    fn red_list_days() {
        let d = |m, day| NaiveDate::from_ymd_opt(2026, m, day).unwrap();
        // Sundays: 18 Oct, 25 Oct, 1 Nov, 8 Nov.
        assert_eq!(red_list_scope(d(10, 25), None), Some(RedScope::All));
        assert_eq!(red_list_scope(d(11, 8), Some("mixed")), Some(RedScope::All));
        assert_eq!(red_list_scope(d(10, 26), Some("earth")), None);
        assert_eq!(
            red_list_scope(d(11, 9), Some("math")),
            Some(RedScope::Subject("math".into()))
        );
        assert_eq!(red_list_scope(d(11, 14), Some("prep")), Some(RedScope::All));
        assert_eq!(red_list_scope(d(11, 15), Some("exam")), None);
    }
}
