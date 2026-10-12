//! The question bank: practice modes (topic, sprint, mixed, Round 1 simulation) with HUSO's
//! scoring. One question per screen, a server-side clock, and a result page.
//!
//! The Error Log (a later feature) reads `answers` of finished attempts where
//! `is_correct = false OR guessed = true`; see [`models::Answer::needs_review`],
//! [`scoring::is_wrong_or_guessed`] and [`engine::finish_attempt`].

pub mod engine;
pub mod models;
pub mod scoring;

use crate::app::content::models::{Subject, Topic};
use models::{Answer, Attempt, ERRORS, MIXED, SIMULATION, SPRINT, TOPIC};
use renox::prelude::*;
use scoring::{SubjectScore, Tally};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub struct Practice;

impl Module for Practice {
    fn name(&self) -> &'static str {
        "practice"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<models::Attempt>();
        app.model::<models::Answer>();
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/practice", index)
            .name("practice.index")
            .post("/practice", start)
            .name("practice.start")
            .get("/practice/{attempt}", show)
            .name("practice.show")
            .post("/practice/{attempt}/answer", answer)
            .name("practice.answer")
            .post("/practice/{attempt}/finish", finish)
            .name("practice.finish")
            .get("/practice/{attempt}/result", result)
            .name("practice.result")
            .require_auth()
    }
}

// ---- Access ----------------------------------------------------------------------------

fn is_parent(user: &User) -> bool {
    user.has_role("parent")
}

/// The student's own attempt, or (for the parent, read-only) an attempt of the student.
async fn readable_attempt(db: &Db, user: &User, attempt_id: i64) -> Result<Attempt> {
    let attempt = Attempt::find_or_404(db, attempt_id).await?;
    if attempt.user_id == user.id {
        return Ok(attempt);
    }
    if is_parent(user) && engine::student_user_id(db).await? == Some(attempt.user_id) {
        return Ok(attempt);
    }
    Err(abort(StatusCode::NOT_FOUND, "No such practice."))
}

/// Only the student takes practice: the parent can read results, never start or answer.
fn require_student(user: &User) -> Result {
    abort_if(
        is_parent(user),
        StatusCode::FORBIDDEN,
        "The parent account can only look at results.",
    )
}

fn show_url(attempt_id: i64, number: i64) -> String {
    format!("/practice/{attempt_id}?q={number}")
}

// ---- Tallies ---------------------------------------------------------------------------

fn tally<'a>(answers: impl IntoIterator<Item = &'a Answer>) -> Tally {
    let mut t = Tally::default();
    for a in answers {
        match (&a.choice, a.is_correct) {
            (None, _) => t.blank += 1,
            (Some(_), true) => t.correct += 1,
            (Some(_), false) => t.wrong += 1,
        }
    }
    t
}

#[derive(Serialize)]
struct TallyView {
    correct: i64,
    wrong: i64,
    blank: i64,
    total: i64,
    raw: String,
    percent: String,
    /// 0..=100 for a bar's width.
    width: i64,
}

impl From<Tally> for TallyView {
    fn from(t: Tally) -> Self {
        TallyView {
            correct: t.correct,
            wrong: t.wrong,
            blank: t.blank,
            total: t.total(),
            raw: scoring::format_quarters(t.raw_q()),
            percent: scoring::format_percent(t.percent_bp()),
            width: t.percent_bp() / 100,
        }
    }
}

// ---- Index -----------------------------------------------------------------------------

#[derive(Serialize)]
struct SubjectInfo {
    slug: String,
    name: String,
    color: String,
    emoji: String,
    questions: i64,
    simulation_questions: i64,
}

#[derive(Serialize)]
struct AttemptLine {
    id: i64,
    mode_label: &'static str,
    detail: String,
    when: DateTime,
    tally: TallyView,
}

fn mode_label(mode: &str) -> &'static str {
    match mode {
        TOPIC => "Topic practice",
        SPRINT => "Sprint",
        MIXED => "Mixed",
        SIMULATION => "Round 1 simulation",
        ERRORS => "Redo wrong questions",
        _ => "Practice",
    }
}

async fn index(user: AuthUser, State(db): State<Db>) -> Result<Response> {
    let parent = is_parent(&user);
    let owner = if parent {
        engine::student_user_id(&db).await?
    } else {
        Some(user.id)
    };

    let counts = engine::question_counts(&db).await?;
    let by_topic = engine::question_counts_by_topic(&db).await?;
    let subjects = Subject::query()
        .order_by(Subject::POSITION)
        .get(&db)
        .await?;

    let mut subject_infos = Vec::new();
    for s in &subjects {
        let target = engine::SIMULATION_PLAN
            .iter()
            .find(|(slug, _)| *slug == s.slug)
            .map_or(0, |(_, n)| *n as i64);
        let have = counts.get(&s.slug).copied().unwrap_or(0);
        subject_infos.push(SubjectInfo {
            slug: s.slug.clone(),
            name: s.name.clone(),
            color: s.color.clone(),
            emoji: s.emoji.clone(),
            questions: have,
            simulation_questions: have.min(target),
        });
    }

    let subject_options: Vec<(String, String)> = subject_infos
        .iter()
        .map(|s| {
            (
                s.slug.clone(),
                format!("{} ({} questions)", s.name, s.questions),
            )
        })
        .collect();

    // Subtopics that have questions, as "Biology · Cell division (12 questions)".
    let subtopics = Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::SUBJECT_ID)
        .order_by(Topic::POSITION)
        .get(&db)
        .await?;
    let subject_names: HashMap<i64, &str> =
        subjects.iter().map(|s| (s.id, s.name.as_str())).collect();
    let topic_options: Vec<(String, String)> = subtopics
        .iter()
        .filter_map(|t| {
            let n = by_topic.get(&t.id).copied().unwrap_or(0);
            (n > 0).then(|| {
                (
                    t.id.to_string(),
                    format!(
                        "{} · {} ({n})",
                        subject_names.get(&t.subject_id).copied().unwrap_or(""),
                        t.name
                    ),
                )
            })
        })
        .collect();

    let mut running = None;
    let mut recent = Vec::new();
    if let Some(owner) = owner {
        // A timer that ran out while the page was closed is closed here, before we look.
        let open = Attempt::query()
            .where_(Attempt::USER_ID.eq(owner))
            .where_(Attempt::FINISHED_AT.is_null())
            .order_by_desc(Attempt::ID)
            .get(&db)
            .await?;
        for a in open {
            let a = engine::advance(&db, a.id).await?;
            if !a.is_finished() && running.is_none() {
                running = Some(a);
            }
        }
        let finished = Attempt::query()
            .where_(Attempt::USER_ID.eq(owner))
            .where_(Attempt::FINISHED_AT.is_not_null())
            .order_by_desc(Attempt::ID)
            .limit(10)
            .get(&db)
            .await?;
        let ids: Vec<i64> = finished.iter().map(|a| a.id).collect();
        let answers = Answer::query()
            .where_(Answer::ATTEMPT_ID.is_in(ids))
            .get(&db)
            .await?;
        for a in finished {
            let tally = tally(answers.iter().filter(|x| x.attempt_id == a.id));
            let detail = match (a.subject.as_deref(), a.mode.as_str()) {
                (Some(slug), _) => subject_names_by_slug(&subjects, slug),
                (None, MIXED) => "5 subjects".to_owned(),
                (None, SIMULATION) => "5 sections".to_owned(),
                _ => String::new(),
            };
            recent.push(AttemptLine {
                id: a.id,
                mode_label: mode_label(&a.mode),
                detail,
                when: a.finished_at.unwrap_or(a.started_at),
                tally: tally.into(),
            });
        }
    }

    Ok(view(
        "practice/index.html",
        context! {
            title => "Practice",
            is_parent => parent,
            subjects => subject_infos,
            subject_options,
            topic_options,
            running => running.map(|a| context! { id => a.id, mode_label => mode_label(&a.mode) }),
            recent,
            sprint_default => engine::SPRINT_DEFAULT,
            any_questions => counts.values().sum::<i64>() > 0,
        },
    )
    .into_response())
}

fn subject_names_by_slug(subjects: &[Subject], slug: &str) -> String {
    subjects
        .iter()
        .find(|s| s.slug == slug)
        .map_or_else(|| slug.to_owned(), |s| s.name.clone())
}

// ---- Start -----------------------------------------------------------------------------

#[derive(Deserialize, Validate)]
struct StartForm {
    mode: String,
    topic: Option<i64>,
    /// Topic mode on a subtopic named by its slug (the syllabus map's button).
    topic_slug: Option<String>,
    subject: Option<String>,
    count: Option<i64>,
}

async fn start(
    user: AuthUser,
    State(db): State<Db>,
    Valid(form): Valid<StartForm>,
) -> Result<Response> {
    require_student(&user)?;
    let attempt = match form.mode.as_str() {
        TOPIC => {
            let topic = match (form.topic, form.topic_slug.as_deref()) {
                (Some(id), _) => Some(id),
                (None, Some(slug)) => Topic::query()
                    .where_(Topic::SLUG.eq(slug))
                    .where_(Topic::PARENT_ID.is_not_null())
                    .first(&db)
                    .await?
                    .map(|t| t.id),
                (None, None) => None,
            };
            match topic {
                Some(topic) => engine::start_topic(&db, user.id, topic).await?,
                None => None,
            }
        }
        SPRINT => match form.subject.as_deref() {
            Some(subject) => {
                let count = form.count.unwrap_or(engine::SPRINT_DEFAULT);
                engine::start_sprint(&db, user.id, subject, count).await?
            }
            None => None,
        },
        MIXED => engine::start_mixed(&db, user.id).await?,
        SIMULATION => engine::start_simulation(&db, user.id).await?,
        ERRORS => engine::start_errors(&db, user.id).await?,
        _ => {
            return Err(abort(
                StatusCode::UNPROCESSABLE_ENTITY,
                "Unknown practice mode.",
            ));
        }
    };
    Ok(match attempt {
        Some(a) => Redirect::to(&show_url(a.id, 1)).into_response(),
        None => (
            Toast::warning("There are no questions for that choice yet."),
            Redirect::route("practice.index", &[])?,
        )
            .into_response(),
    })
}

// ---- One question per screen ------------------------------------------------------------

#[derive(Deserialize)]
struct ShowQuery {
    q: Option<i64>,
}

#[derive(Serialize)]
struct ChoiceView {
    letter: &'static str,
    text: String,
    /// "", "selected", "correct" or "wrong" (the last two only when feedback is shown).
    state: &'static str,
}

#[derive(Serialize)]
struct NavItem {
    number: i64,
    label: i64,
    state: &'static str,
    current: bool,
    href: String,
}

async fn show(
    user: AuthUser,
    State(db): State<Db>,
    Path(attempt_id): Path<i64>,
    Query(query): Query<ShowQuery>,
) -> Result<Response> {
    let attempt = readable_attempt(&db, &user, attempt_id).await?;
    let attempt = engine::advance(&db, attempt.id).await?;
    if attempt.is_finished() || attempt.user_id != user.id {
        return Ok(Redirect::route("practice.result", &[&attempt.id])?.into_response());
    }
    let rows = engine::load_rows(&db, attempt.id).await?;
    let (start, count) = attempt.open_range();
    let requested = query.q.map(|q| q - 1);
    let position = requested
        .unwrap_or_else(|| {
            rows.iter()
                .find(|r| r.answer.position >= start && r.answer.answered_at.is_none())
                .map_or(start, |r| r.answer.position)
        })
        .clamp(start, start + count - 1);
    let Some(row) = rows.iter().find(|r| r.answer.position == position) else {
        return Err(abort(StatusCode::NOT_FOUND, "No such question."));
    };

    let feedback = attempt.explains_at_once() && row.answer.answered_at.is_some();
    let chosen = row.answer.choice.clone().unwrap_or_default();
    let choices: Vec<ChoiceView> = row
        .question
        .choices()
        .into_iter()
        .map(|(letter, text)| {
            let state = if feedback && letter == row.question.answer {
                "correct"
            } else if feedback && letter == chosen {
                "wrong"
            } else if letter == chosen {
                "selected"
            } else {
                ""
            };
            ChoiceView {
                letter,
                text: text.to_owned(),
                state,
            }
        })
        .collect();

    let nav: Vec<NavItem> = rows
        .iter()
        .filter(|r| r.answer.position >= start && r.answer.position < start + count)
        .map(|r| {
            let a = &r.answer;
            let state = if a.answered_at.is_none() {
                "open"
            } else if a.choice.is_none() {
                "skipped"
            } else if attempt.explains_at_once() {
                if a.is_correct { "right" } else { "wrong" }
            } else if a.guessed {
                "guessed"
            } else {
                "answered"
            };
            NavItem {
                number: a.position + 1,
                label: a.position - start + 1,
                state,
                current: a.position == position,
                href: show_url(attempt.id, a.position + 1),
            }
        })
        .collect();
    let unanswered = nav.iter().filter(|n| n.state == "open").count();

    let now = renox::db::now();
    let section = attempt.current_section().map(|s| {
        context! {
            number => attempt.section + 1,
            of => attempt.sections.len(),
            name => s.name.clone(),
            last => attempt.section + 1 == attempt.sections.len() as i64,
        }
    });
    let is_last = position == start + count - 1;
    Ok(view(
        "practice/show.html",
        context! {
            title => "Practice",
            attempt_id => attempt.id,
            mode => attempt.mode.clone(),
            mode_label => mode_label(&attempt.mode),
            section,
            remaining => attempt.remaining_secs(now),
            remaining_text => attempt.remaining_secs(now).map(engine::clock),
            number => position - start + 1,
            total => count,
            position_number => position + 1,
            subject => context! { name => row.subject.name.clone(), color => row.subject.color.clone(), emoji => row.subject.emoji.clone() },
            topic_name => row.topic.name.clone(),
            stem => row.question.stem.clone(),
            visual => row.question.visual.clone(),
            choices,
            chosen,
            guessed => row.answer.guessed,
            answered => row.answer.answered_at.is_some(),
            skipped => row.answer.answered_at.is_some() && row.answer.choice.is_none(),
            feedback,
            correct_letter => row.question.answer.clone(),
            was_correct => row.answer.is_correct,
            explanation => row.question.explanation.clone(),
            explanation_visual => row.question.explanation_visual.clone(),
            is_last,
            prev_url => (position > start).then(|| show_url(attempt.id, position)),
            next_url => (!is_last).then(|| show_url(attempt.id, position + 2)),
            this_url => show_url(attempt.id, position + 1),
            nav,
            unanswered,
        },
    )
    .into_response())
}

#[derive(Deserialize, Validate)]
struct AnswerForm {
    /// The question's number in the attempt (1-based).
    q: i64,
    choice: Option<String>,
    #[serde(default)]
    guessed: bool,
    #[serde(default)]
    skip: bool,
}

async fn answer(
    user: AuthUser,
    State(db): State<Db>,
    Path(attempt_id): Path<i64>,
    Valid(form): Valid<AnswerForm>,
) -> Result<Response> {
    require_student(&user)?;
    let attempt = readable_attempt(&db, &user, attempt_id).await?;
    let position = form.q - 1;
    // A skip wins over a choice that was left selected.
    let choice = form
        .choice
        .as_deref()
        .filter(|c| !c.is_empty() && !form.skip);
    if choice.is_none() && !form.skip {
        // Enter without an answer only moves on.
        let attempt = engine::advance(&db, attempt.id).await?;
        let next = if attempt.explains_at_once() || !attempt.is_open(position + 1) {
            position
        } else {
            position + 1
        };
        return Ok(Redirect::to(&show_url(attempt.id, next + 1)).into_response());
    }
    match engine::record_answer(&db, attempt.id, position, choice, form.guessed).await? {
        engine::Recorded::Closed => Ok((
            Toast::warning("That question is closed: time is up for this section."),
            Redirect::route("practice.show", &[&attempt.id])?,
        )
            .into_response()),
        engine::Recorded::Saved => {
            let attempt = engine::advance(&db, attempt.id).await?;
            let next = if attempt.explains_at_once() || !attempt.is_open(position + 1) {
                position
            } else {
                position + 1
            };
            Ok(Redirect::to(&show_url(attempt.id, next + 1)).into_response())
        }
    }
}

async fn finish(
    user: AuthUser,
    State(db): State<Db>,
    Path(attempt_id): Path<i64>,
) -> Result<Response> {
    require_student(&user)?;
    let attempt = readable_attempt(&db, &user, attempt_id).await?;
    let attempt = engine::finish_section(&db, attempt.id).await?;
    if attempt.is_finished() {
        Ok(Redirect::route("practice.result", &[&attempt.id])?.into_response())
    } else {
        Ok(Redirect::route("practice.show", &[&attempt.id])?.into_response())
    }
}

// ---- Result ----------------------------------------------------------------------------

#[derive(Serialize)]
struct SubjectResult {
    slug: String,
    name: String,
    color: String,
    emoji: String,
    #[serde(flatten)]
    tally: TallyView,
    kept: bool,
    dropped: bool,
}

#[derive(Serialize)]
struct ChoiceLine {
    letter: &'static str,
    text: String,
    is_key: bool,
    is_chosen: bool,
}

#[derive(Serialize)]
struct ReviewRow {
    number: i64,
    subject_name: String,
    color: String,
    topic_name: String,
    stem: String,
    visual: Option<String>,
    choices: Vec<ChoiceLine>,
    your: String,
    key: String,
    /// "correct", "wrong" or "blank".
    status: &'static str,
    guessed: bool,
    error_log: bool,
    seconds: i64,
    explanation: String,
    explanation_visual: Option<String>,
}

async fn result(
    user: AuthUser,
    State(db): State<Db>,
    Path(attempt_id): Path<i64>,
) -> Result<Response> {
    let attempt = readable_attempt(&db, &user, attempt_id).await?;
    let attempt = engine::advance(&db, attempt.id).await?;
    if !attempt.is_finished() {
        return if attempt.user_id == user.id && !is_parent(&user) {
            Ok(Redirect::route("practice.show", &[&attempt.id])?.into_response())
        } else {
            Err(abort(
                StatusCode::CONFLICT,
                "This practice is still in progress.",
            ))
        };
    }
    let rows = engine::load_rows(&db, attempt.id).await?;

    // Per subject, in the order of the syllabus.
    let mut order: Vec<&crate::app::content::models::Subject> = Vec::new();
    for r in &rows {
        if !order.iter().any(|s| s.id == r.subject.id) {
            order.push(&r.subject);
        }
    }
    order.sort_by_key(|s| s.position);
    let tallies: Vec<Tally> = order
        .iter()
        .map(|s| {
            tally(
                rows.iter()
                    .filter(|r| r.subject.id == s.id)
                    .map(|r| &r.answer),
            )
        })
        .collect();
    let scores: Vec<SubjectScore> = order
        .iter()
        .zip(&tallies)
        .map(|(s, t)| SubjectScore {
            slug: s.slug.clone(),
            tally: *t,
        })
        .collect();
    let best = attempt.is_simulation().then(|| scoring::best_four(&scores));
    let subjects: Vec<SubjectResult> = order
        .iter()
        .zip(&tallies)
        .enumerate()
        .map(|(i, (s, t))| SubjectResult {
            slug: s.slug.clone(),
            name: s.name.clone(),
            color: s.color.clone(),
            emoji: s.emoji.clone(),
            tally: (*t).into(),
            kept: best.as_ref().is_none_or(|b| b.kept.contains(&i)),
            dropped: best.as_ref().is_some_and(|b| b.dropped == Some(i)),
        })
        .collect();
    let best_view = best.as_ref().map(|b| {
        context! {
            total => scoring::format_percent(b.total_bp),
            out_of => b.kept.len() * 100,
            dropped => b.dropped.map(|i| order[i].name.clone()),
            count => b.kept.len(),
        }
    });
    let overall: TallyView = tally(rows.iter().map(|r| &r.answer)).into();

    let review: Vec<ReviewRow> = rows
        .iter()
        .map(|r| {
            let a = &r.answer;
            let key = r.question.answer.clone();
            let status = match (&a.choice, a.is_correct) {
                (None, _) => "blank",
                (Some(_), true) => "correct",
                (Some(_), false) => "wrong",
            };
            ReviewRow {
                number: a.position + 1,
                subject_name: r.subject.name.clone(),
                color: r.subject.color.clone(),
                topic_name: r.topic.name.clone(),
                stem: r.question.stem.clone(),
                visual: r.question.visual.clone(),
                choices: r
                    .question
                    .choices()
                    .into_iter()
                    .map(|(letter, text)| ChoiceLine {
                        letter,
                        text: text.to_owned(),
                        is_key: letter == key,
                        is_chosen: a.choice.as_deref() == Some(letter),
                    })
                    .collect(),
                your: a.choice.clone().unwrap_or_else(|| "blank".to_owned()),
                key,
                status,
                guessed: a.guessed,
                error_log: a.needs_review(),
                seconds: a.seconds,
                explanation: r.question.explanation.clone(),
                explanation_visual: r.question.explanation_visual.clone(),
            }
        })
        .collect();

    let minutes = attempt
        .finished_at
        .map(|f| ((f - attempt.started_at).num_seconds().max(0) + 30) / 60);
    Ok(view(
        "practice/result.html",
        context! {
            title => "Practice result",
            attempt_id => attempt.id,
            mode_label => mode_label(&attempt.mode),
            is_simulation => attempt.is_simulation(),
            is_parent => is_parent(&user),
            started => attempt.started_at,
            minutes,
            overall,
            subjects,
            best => best_view,
            review,
        },
    )
    .into_response())
}
