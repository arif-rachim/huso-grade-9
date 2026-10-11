//! Imports the validated content bundle into the database. Safe to run again: rows are
//! upserted by `slug` / `key` / `date`, and cards or questions that left the files are
//! archived (never deleted) so the student's progress survives.

use super::files::{ContentBundle, validate};
use super::models::{Flashcard, PlanDay, PlanTask, Question, Subject, Topic};
use renox::chrono::NaiveDate;
use renox::db::Json;
use renox::prelude::*;
use std::collections::{HashMap, HashSet};

/// `create` for a new row (id 0), `save` for an existing one; evaluates to the stored row.
macro_rules! save {
    ($db:expr, $ty:ty, $row:expr) => {{
        let mut row: $ty = $row;
        if row.id() == 0 {
            <$ty>::create($db, row).await?
        } else {
            row.save($db).await?;
            row
        }
    }};
}

/// What an import did, for the command's output.
#[derive(Debug, Default)]
pub struct ImportReport {
    pub subjects: usize,
    pub topics: usize,
    pub subtopics: usize,
    pub plan_days: usize,
    pub plan_tasks: usize,
    pub flashcards: usize,
    pub questions: usize,
    pub archived: usize,
}

pub async fn import(db: &Db, bundle: &ContentBundle) -> Result<ImportReport> {
    let errors = validate(bundle);
    if !errors.is_empty() {
        return Err(abort(
            StatusCode::UNPROCESSABLE_ENTITY,
            format!(
                "The content files have {} problem(s):\n  - {}",
                errors.len(),
                errors.join("\n  - ")
            ),
        ));
    }
    let mut report = ImportReport::default();
    let mut topic_ids: HashMap<String, i64> = HashMap::new();

    for (si, s) in bundle.syllabus.subjects.iter().enumerate() {
        let mut subject = Subject::query()
            .where_(Subject::SLUG.eq(s.slug.as_str()))
            .first(db)
            .await?
            .unwrap_or_default();
        subject.slug = s.slug.clone();
        subject.name = s.name.clone();
        subject.color = s.color.clone();
        subject.emoji = s.emoji.clone();
        subject.level_hint = s.level_hint.clone();
        subject.position = si as i64;
        let subject = save!(db, Subject, subject);
        report.subjects += 1;

        for (ti, t) in s.topics.iter().enumerate() {
            let topic =
                upsert_topic(db, &t.slug, subject.id, None, &t.name, &[], ti as i64).await?;
            report.topics += 1;
            for (ci, c) in t.children.iter().enumerate() {
                let sub = upsert_topic(
                    db,
                    &c.slug,
                    subject.id,
                    Some(topic.id),
                    &c.name,
                    &c.items,
                    ci as i64,
                )
                .await?;
                topic_ids.insert(c.slug.clone(), sub.id);
                report.subtopics += 1;
            }
        }
    }

    for d in &bundle.plan.days {
        let date = NaiveDate::parse_from_str(&d.date, "%Y-%m-%d")
            .map_err(|e| abort(StatusCode::UNPROCESSABLE_ENTITY, e.to_string()))?;
        let mut day = PlanDay::query()
            .where_(PlanDay::DATE.eq(date))
            .first(db)
            .await?
            .unwrap_or_default();
        day.date = date;
        day.phase = d.phase.clone();
        day.minutes = d.minutes;
        day.subject = d.subject.clone();
        day.title = d.title.clone();
        day.issue = d.issue;
        day.new_subtopics = Json(d.new_subtopics.clone());
        let day = save!(db, PlanDay, day);
        report.plan_days += 1;

        // Tasks keep their id by position, so checks made on them survive a re-import.
        let existing = PlanTask::query()
            .where_(PlanTask::PLAN_DAY_ID.eq(day.id))
            .get(db)
            .await?;
        let mut by_position: HashMap<i64, PlanTask> =
            existing.into_iter().map(|t| (t.position, t)).collect();
        let mut position = 0;
        for block in &d.blocks {
            for label in &block.tasks {
                let mut task = by_position.remove(&position).unwrap_or_default();
                task.plan_day_id = day.id;
                task.block_label = block.label.clone();
                task.block_minutes = block.minutes;
                task.block_subtopics = Json(block.subtopics.clone());
                task.label = label.clone();
                task.position = position;
                save!(db, PlanTask, task);
                position += 1;
                report.plan_tasks += 1;
            }
        }
        let leftovers: Vec<PlanTask> = by_position.into_values().collect();
        for mut left in leftovers {
            left.delete(db).await?;
        }
    }

    let mut seen_cards = HashSet::new();
    for file in &bundle.flashcards {
        for c in &file.cards {
            let mut card = Flashcard::query()
                .where_(Flashcard::KEY.eq(c.id.as_str()))
                .first(db)
                .await?
                .unwrap_or_default();
            card.key = c.id.clone();
            card.topic_id = topic_ids[&c.subtopic];
            card.card_type = c.kind.clone();
            card.front = c.front.clone();
            card.back = c.back.clone();
            card.visual = c.visual.clone().filter(|v| !v.is_empty());
            card.sketch_prompt = c.sketch_prompt.clone().filter(|v| !v.trim().is_empty());
            card.payload = Json(renox::serde_json::Value::Object(c.extra.clone()));
            card.tags = Json(c.tags.clone());
            card.origin = "content".to_owned();
            card.archived_at = None;
            save!(db, Flashcard, card);
            seen_cards.insert(c.id.clone());
            report.flashcards += 1;
        }
    }
    // Content cards that left the files are archived; manual cards are never touched.
    let stale = Flashcard::query()
        .where_(Flashcard::ORIGIN.eq("content"))
        .where_(Flashcard::ARCHIVED_AT.is_null())
        .get(db)
        .await?;
    let stale: Vec<Flashcard> = stale
        .into_iter()
        .filter(|c| !seen_cards.contains(&c.key))
        .collect();
    for mut card in stale {
        card.archived_at = Some(renox::db::now());
        card.save(db).await?;
        report.archived += 1;
    }

    let mut seen_questions = HashSet::new();
    for file in &bundle.questions {
        for q in &file.questions {
            let mut question = Question::query()
                .where_(Question::KEY.eq(q.id.as_str()))
                .first(db)
                .await?
                .unwrap_or_default();
            question.key = q.id.clone();
            question.topic_id = topic_ids[&q.subtopic];
            question.difficulty = q.difficulty;
            question.stem = q.stem.clone();
            question.visual = q.visual.clone();
            question.choice_a = q.choices["A"].clone();
            question.choice_b = q.choices["B"].clone();
            question.choice_c = q.choices["C"].clone();
            question.choice_d = q.choices["D"].clone();
            question.choice_e = q.choices["E"].clone();
            question.answer = q.answer.clone();
            question.explanation = q.explanation.clone();
            question.explanation_visual = q.explanation_visual.clone();
            question.source = q.source.clone();
            question.archived_at = None;
            save!(db, Question, question);
            seen_questions.insert(q.id.clone());
            report.questions += 1;
        }
    }
    let stale = Question::query()
        .where_(Question::ARCHIVED_AT.is_null())
        .get(db)
        .await?;
    let stale: Vec<Question> = stale
        .into_iter()
        .filter(|q| !seen_questions.contains(&q.key))
        .collect();
    for mut question in stale {
        question.archived_at = Some(renox::db::now());
        question.save(db).await?;
        report.archived += 1;
    }
    Ok(report)
}

async fn upsert_topic(
    db: &Db,
    slug: &str,
    subject_id: i64,
    parent_id: Option<i64>,
    name: &str,
    items: &[String],
    position: i64,
) -> Result<Topic> {
    let mut topic = Topic::query()
        .where_(Topic::SLUG.eq(slug))
        .first(db)
        .await?
        .unwrap_or_default();
    topic.slug = slug.to_owned();
    topic.subject_id = subject_id;
    topic.parent_id = parent_id;
    topic.name = name.to_owned();
    topic.items = Json(items.to_vec());
    topic.position = position;
    Ok(save!(db, Topic, topic))
}
