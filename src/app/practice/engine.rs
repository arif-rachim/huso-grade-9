//! Starting attempts, the server-side clock, saving answers and closing sections.
//!
//! The server is the only clock: every deadline is computed from `renox::db::now()`, so a
//! browser that is slow, closed or tampered with cannot buy more time.

use super::models::{Answer, Attempt, MIXED, SIMULATION, SPRINT, Section, TOPIC};
use crate::app::content::models::{Question, Subject, Topic};
use renox::db::Json;
use renox::prelude::*;
use std::collections::HashMap;

/// Questions in a topic practice.
pub const TOPIC_QUESTIONS: usize = 10;
/// Default number of questions in a sprint.
pub const SPRINT_DEFAULT: i64 = 20;
pub const SPRINT_MAX: i64 = 100;
/// A mixed practice: 15 questions, 20 minutes.
pub const MIXED_QUESTIONS: usize = 15;
pub const MIXED_SECS: i64 = 20 * 60;
/// Every section of the simulation has its own 36 minutes.
pub const SECTION_SECS: i64 = 36 * 60;
/// Round 1 of 2024: questions per subject, in the order of the simulation.
pub const SIMULATION_PLAN: [(&str, usize); 5] = [
    ("math", 12),
    ("physics", 20),
    ("chemistry", 35),
    ("biology", 40),
    ("earth", 45),
];
/// The longest a single question is allowed to add to `seconds` (a forgotten tab).
const MAX_SECONDS_PER_ANSWER: i64 = 30 * 60;

/// Seconds per question in a sprint: Mathematics 3 min, Biology and Earth Science 0.9 min,
/// the others 1 min.
pub fn sprint_secs_per_question(subject_slug: &str) -> i64 {
    match subject_slug {
        "math" => 180,
        "biology" | "earth" => 54,
        _ => 60,
    }
}

// ---- Choosing questions ---------------------------------------------------------------

#[derive(Debug, Clone)]
struct Candidate {
    id: i64,
    difficulty: i64,
    subject: String,
    /// `None` = never answered by this student, `Some(false)` = last answer wrong.
    last_correct: Option<bool>,
}

impl Candidate {
    /// Never answered first, then answered wrongly, then the rest.
    fn priority(&self) -> u8 {
        match self.last_correct {
            None => 0,
            Some(false) => 1,
            Some(true) => 2,
        }
    }
}

enum Scope {
    All,
    Subject(String),
    Topic(i64),
}

/// Active questions in `scope`, in random order, with how the student did on each.
async fn candidates(db: &Db, user_id: i64, scope: Scope) -> Result<Vec<Candidate>> {
    let mut sql = String::from(
        "SELECT q.id, q.difficulty, s.slug, \
           (SELECT a.is_correct FROM answers a JOIN attempts t ON t.id = a.attempt_id \
             WHERE t.user_id = ? AND a.question_id = q.id AND a.choice IS NOT NULL \
             ORDER BY a.answered_at DESC, a.id DESC LIMIT 1) \
         FROM questions q \
         JOIN topics tp ON tp.id = q.topic_id \
         JOIN subjects s ON s.id = tp.subject_id \
         WHERE q.archived_at IS NULL",
    );
    match &scope {
        Scope::All => {}
        Scope::Subject(_) => sql.push_str(" AND s.slug = ?"),
        Scope::Topic(_) => sql.push_str(" AND q.topic_id = ?"),
    }
    sql.push_str(" ORDER BY RANDOM()");
    let query = renox::db::sql(sql).bind(user_id);
    let query = match &scope {
        Scope::All => query,
        Scope::Subject(slug) => query.bind(slug.as_str()),
        Scope::Topic(id) => query.bind(*id),
    };
    let rows: Vec<(i64, i64, String, Option<i64>)> = query.fetch_as(db).await?;
    Ok(rows
        .into_iter()
        .map(|(id, difficulty, subject, last)| Candidate {
            id,
            difficulty,
            subject,
            last_correct: last.map(|v| v != 0),
        })
        .collect())
}

/// The best `n` by priority (the input is already random inside each priority).
fn take_by_priority(mut pool: Vec<Candidate>, n: usize) -> Vec<Candidate> {
    pool.sort_by_key(Candidate::priority);
    pool.truncate(n);
    pool
}

/// Easy first: difficulty rises gradually within one attempt (stable, so the random order
/// and the interleaving of subjects survive inside one difficulty).
fn rising(mut picked: Vec<Candidate>) -> Vec<i64> {
    picked.sort_by_key(|c| c.difficulty);
    picked.into_iter().map(|c| c.id).collect()
}

/// `n` questions from several subjects, taken in turns (interleaving).
fn interleaved(pool: Vec<Candidate>, n: usize) -> Vec<Candidate> {
    let mut by_subject: Vec<(String, Vec<Candidate>)> = Vec::new();
    for slug in SIMULATION_PLAN.map(|(s, _)| s) {
        let group: Vec<Candidate> = pool.iter().filter(|c| c.subject == slug).cloned().collect();
        if !group.is_empty() {
            by_subject.push((slug.to_owned(), take_by_priority(group, n)));
        }
    }
    let mut picked: Vec<Candidate> = Vec::new();
    let mut round = 0;
    while picked.len() < n {
        let before = picked.len();
        for (_, group) in &by_subject {
            if picked.len() < n && round < group.len() {
                picked.push(group[round].clone());
            }
        }
        if picked.len() == before {
            break;
        }
        round += 1;
    }
    picked
}

// ---- Starting an attempt --------------------------------------------------------------

struct Plan {
    mode: &'static str,
    subject: Option<String>,
    topic_id: Option<i64>,
    ids: Vec<i64>,
    time_limit_secs: Option<i64>,
    sections: Vec<Section>,
}

async fn create_attempt(db: &Db, user_id: i64, plan: Plan) -> Result<Attempt> {
    let now = renox::db::now();
    let simulation = plan.mode == SIMULATION;
    let attempt = Attempt::create(
        db,
        Attempt {
            user_id,
            mode: plan.mode.to_owned(),
            subject: plan.subject,
            topic_id: plan.topic_id,
            started_at: now,
            time_limit_secs: plan.time_limit_secs,
            question_ids: Json(plan.ids.clone()),
            sections: Json(plan.sections),
            section_started_at: simulation.then_some(now),
            last_activity_at: Some(now),
            ..Default::default()
        },
    )
    .await?;
    let rows = plan
        .ids
        .iter()
        .enumerate()
        .map(|(position, question_id)| Answer {
            attempt_id: attempt.id,
            question_id: *question_id,
            position: position as i64,
            ..Default::default()
        })
        .collect::<Vec<_>>();
    Answer::insert_many(db, rows).await?;
    Ok(attempt)
}

/// Topic practice: 10 questions of one subtopic, no timer, an explanation after each answer.
pub async fn start_topic(db: &Db, user_id: i64, topic_id: i64) -> Result<Option<Attempt>> {
    let pool = candidates(db, user_id, Scope::Topic(topic_id)).await?;
    let subject = match Topic::find(db, topic_id).await? {
        Some(topic) => Subject::find(db, topic.subject_id).await?.map(|s| s.slug),
        None => None,
    };
    let ids = rising(take_by_priority(pool, TOPIC_QUESTIONS));
    if ids.is_empty() {
        return Ok(None);
    }
    let plan = Plan {
        mode: TOPIC,
        subject,
        topic_id: Some(topic_id),
        ids,
        time_limit_secs: None,
        sections: Vec::new(),
    };
    Ok(Some(create_attempt(db, user_id, plan).await?))
}

/// Sprint: `count` questions of one subject against the clock.
pub async fn start_sprint(
    db: &Db,
    user_id: i64,
    subject: &str,
    count: i64,
) -> Result<Option<Attempt>> {
    let count = count.clamp(1, SPRINT_MAX) as usize;
    let pool = candidates(db, user_id, Scope::Subject(subject.to_owned())).await?;
    let ids = rising(take_by_priority(pool, count));
    if ids.is_empty() {
        return Ok(None);
    }
    let secs = ids.len() as i64 * sprint_secs_per_question(subject);
    let plan = Plan {
        mode: SPRINT,
        subject: Some(subject.to_owned()),
        topic_id: None,
        ids,
        time_limit_secs: Some(secs),
        sections: Vec::new(),
    };
    Ok(Some(create_attempt(db, user_id, plan).await?))
}

/// Mixed: 15 questions from the five subjects in turns, 20 minutes.
pub async fn start_mixed(db: &Db, user_id: i64) -> Result<Option<Attempt>> {
    let pool = candidates(db, user_id, Scope::All).await?;
    let mut picked = interleaved(pool.clone(), MIXED_QUESTIONS);
    if picked.len() < MIXED_QUESTIONS {
        // Fewer than five subjects have questions, or a subject ran dry: fill from the rest.
        let have: Vec<i64> = picked.iter().map(|c| c.id).collect();
        let rest: Vec<Candidate> = pool.into_iter().filter(|c| !have.contains(&c.id)).collect();
        picked.extend(take_by_priority(rest, MIXED_QUESTIONS - picked.len()));
    }
    let ids = rising(picked);
    if ids.is_empty() {
        return Ok(None);
    }
    let plan = Plan {
        mode: MIXED,
        subject: None,
        topic_id: None,
        ids,
        time_limit_secs: Some(MIXED_SECS),
        sections: Vec::new(),
    };
    Ok(Some(create_attempt(db, user_id, plan).await?))
}

/// Round 1 simulation: five consecutive sections of 36 minutes. A subject without questions
/// is left out; a subject with fewer than the 2024 paper has all it has.
pub async fn start_simulation(db: &Db, user_id: i64) -> Result<Option<Attempt>> {
    let pool = candidates(db, user_id, Scope::All).await?;
    let names: HashMap<String, String> = Subject::query()
        .get(db)
        .await?
        .into_iter()
        .map(|s| (s.slug, s.name))
        .collect();
    let mut ids: Vec<i64> = Vec::new();
    let mut sections: Vec<Section> = Vec::new();
    for (slug, target) in SIMULATION_PLAN {
        let group: Vec<Candidate> = pool.iter().filter(|c| c.subject == slug).cloned().collect();
        let section_ids = rising(take_by_priority(group, target));
        if section_ids.is_empty() {
            continue;
        }
        sections.push(Section {
            subject: slug.to_owned(),
            name: names.get(slug).cloned().unwrap_or_else(|| slug.to_owned()),
            start: ids.len() as i64,
            count: section_ids.len() as i64,
            secs: SECTION_SECS,
        });
        ids.extend(section_ids);
    }
    if ids.is_empty() {
        return Ok(None);
    }
    let plan = Plan {
        mode: SIMULATION,
        subject: None,
        topic_id: None,
        ids,
        time_limit_secs: None,
        sections,
    };
    Ok(Some(create_attempt(db, user_id, plan).await?))
}

// ---- The clock ------------------------------------------------------------------------

/// Blank every question of `start..start+count` that has no answer yet.
async fn blank_unanswered(
    db: &Db,
    attempt_id: i64,
    start: i64,
    count: i64,
    at: DateTime,
) -> Result<()> {
    renox::db::sql(
        "UPDATE answers SET answered_at = ?, choice = NULL, is_correct = 0, guessed = 0, \
         updated_at = ? WHERE attempt_id = ? AND answered_at IS NULL \
         AND position >= ? AND position < ?",
    )
    .bind(at)
    .bind(at)
    .bind(attempt_id)
    .bind(start)
    .bind(start + count)
    .execute(db)
    .await?;
    Ok(())
}

/// Close the running section at `at`: its open questions become blank, then the next section
/// starts at `at`, or (the last section, or any other mode) the attempt is finished.
async fn close_section(db: &Db, mut attempt: Attempt, at: DateTime) -> Result<Attempt> {
    let (start, count) = attempt.open_range();
    blank_unanswered(db, attempt.id, start, count, at).await?;
    if attempt.is_simulation() && (attempt.section + 1) < attempt.sections.len() as i64 {
        attempt.section += 1;
        attempt.section_started_at = Some(at);
        attempt.last_activity_at = Some(at);
        attempt.save(db).await?;
        Ok(attempt)
    } else {
        finish_at(db, attempt, at).await
    }
}

async fn finish_at(db: &Db, mut attempt: Attempt, at: DateTime) -> Result<Attempt> {
    if attempt.is_finished() {
        return Ok(attempt);
    }
    blank_unanswered(db, attempt.id, 0, attempt.len(), at).await?;
    attempt.finished_at = Some(at);
    attempt.save(db).await?;
    Ok(attempt)
}

/// Load an attempt and apply the clock: a section or attempt whose time is over is closed
/// (its open questions are recorded as blank) before the attempt is returned. Call it first in
/// every handler that shows or changes an attempt.
pub async fn advance(db: &Db, attempt_id: i64) -> Result<Attempt> {
    let mut attempt = Attempt::find_or_404(db, attempt_id).await?;
    let now = renox::db::now();
    while let Some(deadline) = attempt.deadline() {
        if now < deadline {
            break;
        }
        attempt = close_section(db, attempt, deadline).await?;
    }
    Ok(attempt)
}

/// Finish an attempt now: every question without an answer is recorded as blank. Safe to call
/// again. After this, `answers` is complete: one row per question with `choice`, `is_correct`,
/// `guessed` and `seconds`.
pub async fn finish_attempt(db: &Db, attempt_id: i64) -> Result<Attempt> {
    let attempt = advance(db, attempt_id).await?;
    finish_at(db, attempt, renox::db::now()).await
}

/// End the running section early (a simulation goes on with the next one, other modes finish).
pub async fn finish_section(db: &Db, attempt_id: i64) -> Result<Attempt> {
    let attempt = advance(db, attempt_id).await?;
    if attempt.is_finished() {
        return Ok(attempt);
    }
    close_section(db, attempt, renox::db::now()).await
}

// ---- Answering ------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Recorded {
    Saved,
    /// Time ran out, the section is over, or (topic mode) the question was already answered.
    Closed,
}

/// Save the student's choice (`None` = skip / blank) for the question at `position`.
pub async fn record_answer(
    db: &Db,
    attempt_id: i64,
    position: i64,
    choice: Option<&str>,
    guessed: bool,
) -> Result<Recorded> {
    let mut attempt = advance(db, attempt_id).await?;
    if !attempt.is_open(position) {
        return Ok(Recorded::Closed);
    }
    let mut answer = Answer::query()
        .where_(Answer::ATTEMPT_ID.eq(attempt.id))
        .where_(Answer::POSITION.eq(position))
        .first_or_404(db)
        .await?;
    if attempt.explains_at_once() && answer.answered_at.is_some() {
        return Ok(Recorded::Closed);
    }
    let choice = choice.map(str::to_ascii_uppercase);
    if let Some(letter) = &choice {
        abort_unless(
            matches!(letter.as_str(), "A" | "B" | "C" | "D" | "E"),
            StatusCode::UNPROCESSABLE_ENTITY,
            "Choose A, B, C, D or E.",
        )?;
    }
    let question = Question::find_or_404(db, answer.question_id).await?;
    let now = renox::db::now();
    let since = [attempt.last_activity_at, attempt.section_started_at]
        .into_iter()
        .flatten()
        .max()
        .unwrap_or(attempt.started_at);
    answer.seconds += (now - since).num_seconds().clamp(0, MAX_SECONDS_PER_ANSWER);
    answer.is_correct = choice.as_deref() == Some(question.answer.as_str());
    answer.guessed = guessed && choice.is_some();
    answer.choice = choice;
    answer.answered_at = Some(now);
    answer.save(db).await?;
    attempt.last_activity_at = Some(now);
    attempt.save(db).await?;
    Ok(Recorded::Saved)
}

// ---- Reading ---------------------------------------------------------------------------

/// An answer with its question, subtopic and subject.
#[derive(Debug, Clone)]
pub struct Row {
    pub answer: Answer,
    pub question: Question,
    pub topic: Topic,
    pub subject: Subject,
}

/// Every answer of an attempt in question order, with what it refers to (4 queries).
pub async fn load_rows(db: &Db, attempt_id: i64) -> Result<Vec<Row>> {
    let answers = Answer::query()
        .where_(Answer::ATTEMPT_ID.eq(attempt_id))
        .order_by(Answer::POSITION)
        .get(db)
        .await?;
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
    let mut rows = Vec::with_capacity(answers.len());
    for answer in answers {
        let Some(question) = questions.get(&answer.question_id).cloned() else {
            continue;
        };
        let Some(topic) = topics.get(&question.topic_id).cloned() else {
            continue;
        };
        let Some(subject) = subjects.get(&topic.subject_id).cloned() else {
            continue;
        };
        rows.push(Row {
            answer,
            question,
            topic,
            subject,
        });
    }
    Ok(rows)
}

/// Active questions per subject slug.
pub async fn question_counts(db: &Db) -> Result<HashMap<String, i64>> {
    let rows: Vec<(String, i64)> = renox::db::sql(
        "SELECT s.slug, COUNT(*) FROM questions q \
         JOIN topics tp ON tp.id = q.topic_id JOIN subjects s ON s.id = tp.subject_id \
         WHERE q.archived_at IS NULL GROUP BY s.slug",
    )
    .fetch_as(db)
    .await?;
    Ok(rows.into_iter().collect())
}

/// Active questions per subtopic id.
pub async fn question_counts_by_topic(db: &Db) -> Result<HashMap<i64, i64>> {
    let rows: Vec<(i64, i64)> = renox::db::sql(
        "SELECT topic_id, COUNT(*) FROM questions WHERE archived_at IS NULL GROUP BY topic_id",
    )
    .fetch_as(db)
    .await?;
    Ok(rows.into_iter().collect())
}

/// The student of the household (the parent reads their data).
pub async fn student_user_id(db: &Db) -> Result<Option<i64>> {
    Ok(renox::db::sql(
        "SELECT u.id FROM users u JOIN role_user ru ON ru.user_id = u.id \
         JOIN roles r ON r.id = ru.role_id WHERE r.name = 'student' ORDER BY u.id LIMIT 1",
    )
    .scalar_optional(db)
    .await?)
}

/// Seconds as `m:ss` (or `h:mm:ss`).
pub fn clock(secs: i64) -> String {
    let secs = secs.max(0);
    let (h, m, s) = (secs / 3600, (secs % 3600) / 60, secs % 60);
    if h > 0 {
        format!("{h}:{m:02}:{s:02}")
    } else {
        format!("{m}:{s:02}")
    }
}
