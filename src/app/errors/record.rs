//! Filling the Error Log: automatically from a finished attempt.

use super::leitner;
use super::models::{ErrorEntry, OPEN, ORIGIN_ATTEMPT};
use crate::app::content::models::Subject;
use crate::app::content::models::{Question, Topic};
use crate::app::practice::models::{Answer, Attempt};
use renox::prelude::*;
use std::collections::{HashMap, HashSet};

/// Log the mistakes of a finished attempt: every wrong answer and every correct-but-guessed
/// answer becomes an entry (box 1, due tomorrow; cause `guess` when guessed). Blank answers
/// are not logged. A question that already has an open entry is not duplicated: that entry goes
/// back to box 1. Safe to call twice: an answer that already has an entry is skipped.
///
/// Returns how many answers were logged.
pub async fn record_attempt(db: &Db, attempt_id: i64) -> Result<usize> {
    let attempt = Attempt::find_or_404(db, attempt_id).await?;
    if !attempt.is_finished() {
        return Ok(0);
    }
    let answers: Vec<Answer> = Answer::query()
        .where_(Answer::ATTEMPT_ID.eq(attempt_id))
        .order_by(Answer::POSITION)
        .get(db)
        .await?
        .into_iter()
        .filter(|a| !a.is_blank() && a.needs_review())
        .collect();
    if answers.is_empty() {
        return Ok(0);
    }
    let done: HashSet<i64> = ErrorEntry::query()
        .where_(ErrorEntry::ANSWER_ID.is_in(answers.iter().map(|a| a.id)))
        .get(db)
        .await?
        .into_iter()
        .filter_map(|e| e.answer_id)
        .collect();
    let questions: HashMap<i64, Question> =
        Question::find_many(db, answers.iter().map(|a| a.question_id))
            .await?
            .into_iter()
            .map(|q| (q.id, q))
            .collect();
    let topics: HashMap<i64, Topic> = Topic::find_many(db, questions.values().map(|q| q.topic_id))
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

    let due = leitner::due_on(crate::clock::today(), 1);
    let mut logged = 0;
    for answer in answers {
        if done.contains(&answer.id) {
            continue;
        }
        let Some(question) = questions.get(&answer.question_id) else {
            continue;
        };
        let Some(topic) = topics.get(&question.topic_id) else {
            continue;
        };
        let Some(subject) = subjects.get(&topic.subject_id) else {
            continue;
        };
        let open = ErrorEntry::query()
            .where_(ErrorEntry::USER_ID.eq(attempt.user_id))
            .where_(ErrorEntry::QUESTION_ID.eq(question.id))
            .where_(ErrorEntry::STATUS.eq(OPEN))
            .first(db)
            .await?;
        match open {
            Some(mut entry) => {
                entry.box_no = 1;
                entry.due_on = due;
                entry.answer_id = Some(answer.id);
                if answer.guessed && !entry.has_cause() {
                    entry.cause = Some("guess".into());
                }
                entry.save(db).await?;
            }
            None => {
                ErrorEntry::create(
                    db,
                    ErrorEntry {
                        user_id: attempt.user_id,
                        origin: ORIGIN_ATTEMPT.into(),
                        answer_id: Some(answer.id),
                        question_id: Some(question.id),
                        topic_id: topic.id,
                        subject: subject.slug.clone(),
                        cause: answer.guessed.then(|| "guess".to_owned()),
                        box_no: 1,
                        due_on: due,
                        status: OPEN.into(),
                        ..Default::default()
                    },
                )
                .await?;
            }
        }
        logged += 1;
    }
    Ok(logged)
}
