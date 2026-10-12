//! The syllabus map: every subtopic as a tile coloured by mastery (grey = not started,
//! red < 40, yellow 40-69, green >= 70), and a page per subtopic with the breakdown and the
//! buttons that open practice and flashcards on just that subtopic.
//!
//! The student and the parent see the same map (the parent reads the student's numbers).
//! [`mastery_by_subtopic`] is used by the Parent dashboard and by the READY status of the lessons.

pub mod mastery;

use crate::app::accounts::{PARENT, STUDENT};
use crate::app::content::models::{Lesson, Subject, Topic};
use crate::app::errors::models::{ErrorEntry, OPEN, cause_label};
use crate::app::practice::engine::student_user_id;
use mastery::{Evidence, band};
use renox::prelude::*;
use serde::Deserialize;

use std::collections::HashMap;

pub struct Syllabus;

impl Module for Syllabus {
    fn name(&self) -> &'static str {
        "syllabus"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/syllabus", index)
            .name("syllabus.index")
            .get("/syllabus/{slug}", show)
            .name("syllabus.show")
    }
}

/// Mastery (0-100, `None` = not started) of every subtopic of the syllabus, by subtopic slug.
/// A constant number of queries.
pub async fn mastery_by_subtopic(db: &Db, user_id: i64) -> Result<HashMap<String, Option<i32>>> {
    let evidence = mastery::load(db, user_id).await?;
    let subtopics = Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .get(db)
        .await?;
    Ok(subtopics
        .into_iter()
        .map(|t| {
            let value = evidence.get(&t.id).and_then(mastery::mastery);
            (t.slug, value)
        })
        .collect())
}

/// The same, keyed by topic id (only the started subtopics).
pub async fn mastery_by_topic_id(db: &Db, user_id: i64) -> Result<HashMap<i64, i32>> {
    let evidence = mastery::load(db, user_id).await?;
    Ok(evidence
        .into_iter()
        .filter_map(|(id, e)| mastery::mastery(&e).map(|v| (id, v)))
        .collect())
}

/// Whose numbers this user sees: their own, or (for the parent) the student's.
async fn owner_id(db: &Db, user: &User) -> Result<Option<i64>> {
    if user.has_role(PARENT) {
        student_user_id(db).await
    } else {
        Ok(Some(user.id))
    }
}

fn label(value: Option<i32>) -> String {
    value.map_or_else(|| "–".to_owned(), |v| format!("{v}%"))
}

fn band_name(band: &str) -> &'static str {
    match band {
        "red" => "Weak",
        "yellow" => "Getting there",
        "green" => "Strong",
        _ => "Not started",
    }
}

#[derive(Deserialize, Default)]
struct Filter {
    only: Option<String>,
}

async fn index(
    State(db): State<Db>,
    user: Option<AuthUser>,
    Query(filter): Query<Filter>,
) -> Result<View> {
    let guest = user.is_none();
    let weak_only = filter.only.as_deref() == Some("weak");
    // A guest sees the map with every tile grey: no personal mastery.
    let evidence = match &user {
        Some(user) => match owner_id(&db, user).await? {
            Some(owner) => mastery::load(&db, owner).await?,
            None => HashMap::new(),
        },
        None => HashMap::new(),
    };
    let subjects = Subject::query()
        .order_by(Subject::POSITION)
        .get(&db)
        .await?;
    let topics = Topic::query()
        .order_by(Topic::SUBJECT_ID)
        .order_by(Topic::POSITION)
        .get(&db)
        .await?;

    let mut columns = Vec::new();
    for subject in &subjects {
        let mut sum = 0i64;
        let mut started = 0i64;
        let mut counts: HashMap<&str, i64> = HashMap::new();
        let mut groups = Vec::new();
        for topic in topics
            .iter()
            .filter(|t| t.subject_id == subject.id && t.parent_id.is_none())
        {
            let mut tiles = Vec::new();
            for sub in topics.iter().filter(|t| t.parent_id == Some(topic.id)) {
                let value = evidence.get(&sub.id).and_then(mastery::mastery);
                let b = band(value);
                *counts.entry(b).or_default() += 1;
                if let Some(v) = value {
                    sum += i64::from(v);
                    started += 1;
                }
                if weak_only && !matches!(b, "red" | "grey") {
                    continue;
                }
                tiles.push(json!({
                    "slug": sub.slug,
                    "name": sub.name,
                    "value": label(value),
                    "band": b,
                    "band_name": band_name(b),
                }));
            }
            if !tiles.is_empty() {
                groups.push(json!({ "name": topic.name, "tiles": tiles }));
            }
        }
        let average = (started > 0).then(|| (sum + started / 2) / started);
        let count = |k: &str| counts.get(k).copied().unwrap_or(0);
        columns.push(json!({
            "slug": subject.slug,
            "name": subject.name,
            "emoji": subject.emoji,
            "color": subject.color,
            "average": average.map_or_else(|| "–".to_owned(), |a| format!("{a}%")),
            "green": count("green"),
            "yellow": count("yellow"),
            "red": count("red"),
            "grey": count("grey"),
            "groups": groups,
        }));
    }
    Ok(view(
        "syllabus/index.html",
        context! { title => "Syllabus map", columns, weak_only, guest },
    ))
}

/// `(title, url)` links for a subject from `content/sources.json` (the "visual" resources).
fn visual_links(subject: &str) -> Vec<renox::serde_json::Value> {
    let path = crate::app::content::project_dir().join("content/sources.json");
    let Ok(text) = std::fs::read_to_string(path) else {
        return vec![];
    };
    let Ok(data) = renox::serde_json::from_str::<renox::serde_json::Value>(&text) else {
        return vec![];
    };
    data["visual"][subject]
        .as_array()
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .filter(|l| l["title"].is_string() && l["url"].is_string())
        .collect()
}

async fn show(
    State(db): State<Db>,
    user: Option<AuthUser>,
    Path(slug): Path<String>,
) -> Result<View> {
    let topic = Topic::query()
        .where_(Topic::SLUG.eq(slug.as_str()))
        .where_(Topic::PARENT_ID.is_not_null())
        .first_or_404(&db)
        .await?;
    let subject = Subject::find_or_404(&db, topic.subject_id).await?;
    let parent_topic = match topic.parent_id {
        Some(id) => Topic::find(&db, id).await?,
        None => None,
    };
    let guest = user.is_none();
    let owner = match &user {
        Some(user) => owner_id(&db, user).await?,
        None => None,
    };

    let evidence: Evidence = match owner {
        Some(owner) => mastery::load(&db, owner)
            .await?
            .get(&topic.id)
            .copied()
            .unwrap_or_default(),
        None => Evidence::default(),
    };
    let value = mastery::mastery(&evidence);
    let b = band(value);

    // Cards per Leitner box (weakest part of a card), plus the ones not reviewed yet.
    let mut boxes = [0i64; 5];
    if let Some(owner) = owner {
        let rows: Vec<(i64, i64)> = renox::db::sql(
            "SELECT m.min_box, COUNT(*) FROM flashcards f \
             JOIN (SELECT flashcard_id, MIN(box) AS min_box FROM card_states \
                   WHERE user_id = ? GROUP BY flashcard_id) m ON m.flashcard_id = f.id \
             WHERE f.topic_id = ? AND f.archived_at IS NULL GROUP BY m.min_box",
        )
        .bind(owner)
        .bind(topic.id)
        .fetch_as(&db)
        .await?;
        for (box_no, n) in rows {
            if (1..=5).contains(&box_no) {
                boxes[(box_no - 1) as usize] = n;
            }
        }
    }
    let new_cards = (evidence.cards - evidence.reviewed).max(0);

    // Open entries of the Error Log for this subtopic.
    let errors: Vec<_> = match owner {
        Some(owner) => ErrorEntry::query()
            .where_(ErrorEntry::USER_ID.eq(owner))
            .where_(ErrorEntry::TOPIC_ID.eq(topic.id))
            .where_(ErrorEntry::STATUS.eq(OPEN))
            .order_by(ErrorEntry::DUE_ON)
            .get(&db)
            .await?
            .into_iter()
            .map(|e| {
                json!({
                    "id": e.id,
                    "cause": e.cause.as_deref().map_or("Cause not set", cause_label),
                    "due_on": e.due_on.format("%a %-d %b").to_string(),
                    "note": e.note,
                })
            })
            .collect(),
        None => vec![],
    };

    let has_lesson = Lesson::query()
        .where_(Lesson::TOPIC_ID.eq(topic.id))
        .first(&db)
        .await?
        .is_some();

    let subtitle = match &parent_topic {
        Some(p) => format!("{} {} · {}", subject.emoji, subject.name, p.name),
        None => format!("{} {}", subject.emoji, subject.name),
    };
    Ok(view(
        "syllabus/show.html",
        context! {
            title => topic.name.clone(),
            subtitle,
            topic,
            parent_topic,
            subject => subject.clone(),
            value => label(value),
            has_value => value.is_some(),
            band => b,
            band_name => band_name(b),
            accuracy => evidence.accuracy_percent(),
            answers => evidence.answers,
            window_days => mastery::WINDOW_DAYS,
            cards => evidence.cards,
            known => evidence.known,
            boxes,
            new_cards,
            open_errors => errors,
            has_lesson,
            links => visual_links(&subject.slug),
            is_student => user.as_ref().is_some_and(|u| u.has_role(STUDENT)),
            guest,
        },
    ))
}
