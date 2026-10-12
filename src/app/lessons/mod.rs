//! Materials: the visual lessons (`materi/<subject>/*.md`) in the app.
//!
//! `/lessons` lists them per subject in schedule order with their READY status; `/lessons/{slug}`
//! shows one lesson, the "I redrew it from memory" mark and an interactive "Check your
//! understanding". The student saves marks and checks; the parent sees the same pages and the
//! same statuses, read-only.

pub mod render;
pub mod status;

use crate::app::content::lesson_file::{CheckQuestion, parse_lesson};
use crate::app::content::models::{Lesson, Subject, Topic};
use renox::chrono::NaiveDate;
use renox::db::Json;
use renox::prelude::*;
use serde::{Deserialize, Serialize};
use status::{Status, TopicState};
use std::collections::HashMap;

pub const STUDENT: &str = "student";
pub const PARENT: &str = "parent";

pub struct Lessons;

/// What the student did on a lesson: a "redrew it" mark (`score` is empty) or a check (0-5).
#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "lesson_checks")]
pub struct LessonCheck {
    pub id: i64,
    pub user_id: i64,
    pub topic_id: i64,
    pub score: Option<i64>,
    pub drawn: bool,
    /// The letters the student chose: `{"1": "B", ...}`.
    pub answers: Json<HashMap<String, String>>,
    pub checked_on: NaiveDate,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl Module for Lessons {
    fn name(&self) -> &'static str {
        "lessons"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<LessonCheck>();
        app.view_data::<IndexPage>();
        app.view_data::<ShowPage>();
    }

    fn routes(&self) -> Routes {
        // Student and parent read.
        let shared = Routes::new()
            .get("/lessons", index)
            .name("lessons.index")
            .get("/lessons/{slug}", show)
            .name("lessons.show")
            .require_auth();
        // Only the student saves.
        let student = Routes::new()
            .post("/lessons/{slug}/drawn", mark_drawn)
            .name("lessons.drawn")
            .post("/lessons/{slug}/check", check)
            .name("lessons.check")
            .require_role(STUDENT);
        shared.merge(student)
    }
}

/// The student whose data this user sees: themselves, or (for the parent) the household's student.
pub async fn student_id(db: &Db, user: &AuthUser) -> Result<Option<i64>> {
    if user.has_role(STUDENT) {
        return Ok(Some(user.id));
    }
    Ok(renox::db::sql(
        "SELECT ru.user_id FROM role_user ru JOIN roles r ON r.id = ru.role_id \
         WHERE r.name = 'student' ORDER BY ru.user_id LIMIT 1",
    )
    .scalar_optional(db)
    .await?)
}

// ---------------------------------------------------------------------------------------------
// Index

#[derive(Serialize)]
struct IndexItem {
    slug: String,
    name: String,
    scheduled: Option<String>,
    best_score: Option<i64>,
    drawn: bool,
    status: Status,
    status_label: &'static str,
    status_icon: &'static str,
    status_kind: &'static str,
}

#[derive(Serialize)]
struct IndexGroup {
    name: String,
    emoji: String,
    color: String,
    ready: usize,
    total: usize,
    items: Vec<IndexItem>,
}

#[derive(Serialize, ViewData)]
#[view(template = "lessons/index.html")]
struct IndexPage {
    title: &'static str,
    is_parent: bool,
    groups: Vec<IndexGroup>,
    ready: usize,
    total: usize,
}

async fn index(State(db): State<Db>, user: AuthUser) -> Result<View> {
    let student = student_id(&db, &user).await?;
    let states = match student {
        Some(id) => status::states(&db, id).await?,
        None => HashMap::new(),
    };
    let scheduled = status::scheduled_dates(&db).await?;
    let subjects = Subject::query()
        .order_by(Subject::POSITION)
        .get(&db)
        .await?;
    let lessons = Lesson::query().get(&db).await?;
    let topics: HashMap<i64, Topic> = Topic::query()
        .where_(Topic::ID.is_in(lessons.iter().map(|l| l.topic_id).collect::<Vec<_>>()))
        .get(&db)
        .await?
        .into_iter()
        .map(|t| (t.id, t))
        .collect();

    let mut groups = Vec::new();
    for subject in subjects {
        // Schedule order; the lessons that are not scheduled come last, in syllabus order.
        let mut mine: Vec<&Topic> = topics
            .values()
            .filter(|t| t.subject_id == subject.id)
            .collect();
        mine.sort_by_key(|t| (scheduled.get(&t.slug).copied(), t.position, t.id));
        let items: Vec<IndexItem> = mine
            .into_iter()
            .map(|t| {
                let state = states.get(&t.id).copied().unwrap_or(TopicState::NONE);
                IndexItem {
                    slug: t.slug.clone(),
                    name: t.name.clone(),
                    scheduled: scheduled
                        .get(&t.slug)
                        .map(|d| d.format("%a %-d %b").to_string()),
                    best_score: state.best_score,
                    drawn: state.drawn,
                    status: state.status,
                    status_label: state.status.label(),
                    status_icon: state.status.icon(),
                    status_kind: state.status.kind(),
                }
            })
            .collect();
        if items.is_empty() {
            continue;
        }
        groups.push(IndexGroup {
            name: subject.name,
            emoji: subject.emoji,
            color: subject.color,
            ready: items.iter().filter(|i| i.status == Status::Ready).count(),
            total: items.len(),
            items,
        });
    }
    let ready = groups.iter().map(|g| g.ready).sum();
    let total = groups.iter().map(|g| g.total).sum();
    Ok(View::typed(IndexPage {
        title: "Materials",
        is_parent: !user.has_role(STUDENT),
        groups,
        ready,
        total,
    }))
}

// ---------------------------------------------------------------------------------------------
// One lesson

#[derive(Serialize)]
struct QuestionView {
    number: usize,
    /// `q1` ... `q5`: the field name.
    field: String,
    text_html: String,
    /// `[letter, "A. text"]` for the radio group.
    options: Vec<(String, String)>,
    /// The letter chosen in the last check.
    chosen: Option<String>,
    /// Filled once the student has checked: right or wrong, and why.
    result: Option<QuestionResult>,
}

#[derive(Serialize)]
struct QuestionResult {
    correct: bool,
    answer: String,
    explanation_html: String,
}

#[derive(Serialize)]
struct Attempt {
    score: i64,
    on: String,
    passed: bool,
}

#[derive(Serialize)]
struct WatchView {
    label: String,
    url: String,
    note: String,
}

#[derive(Serialize, ViewData)]
#[view(template = "lessons/show.html")]
struct ShowPage {
    title: String,
    slug: String,
    subject_name: String,
    color: String,
    emoji: String,
    is_parent: bool,
    body_html: String,
    key_html: String,
    watch: Vec<WatchView>,
    questions: Vec<QuestionView>,
    drawn: bool,
    best_score: Option<i64>,
    status: Status,
    status_label: &'static str,
    status_icon: &'static str,
    status_kind: &'static str,
    scheduled: Option<String>,
    last_attempt: Option<Attempt>,
    pass_score: i64,
}

async fn find_lesson(db: &Db, slug: &str) -> Result<(Topic, Lesson, Subject)> {
    let topic = Topic::query()
        .where_(Topic::SLUG.eq(slug))
        .first_or_404(db)
        .await?;
    let lesson = Lesson::query()
        .where_(Lesson::TOPIC_ID.eq(topic.id))
        .first_or_404(db)
        .await?;
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    Ok((topic, lesson, subject))
}

fn question_views(questions: &[CheckQuestion], last: Option<&LessonCheck>) -> Vec<QuestionView> {
    questions
        .iter()
        .map(|q| {
            let chosen = last
                .and_then(|c| c.answers.0.get(&q.number.to_string()))
                .cloned();
            let result = last.map(|_| QuestionResult {
                correct: chosen.as_deref() == Some(q.answer.as_str()),
                answer: q.answer.clone(),
                explanation_html: render::render_markdown(&q.explanation),
            });
            QuestionView {
                number: q.number,
                field: format!("q{}", q.number),
                text_html: render::render_markdown(&q.text),
                options: q
                    .choices
                    .iter()
                    .map(|(letter, text)| (letter.clone(), format!("{letter}. {text}")))
                    .collect(),
                chosen,
                result,
            }
        })
        .collect()
}

async fn show(State(db): State<Db>, user: AuthUser, Path(slug): Path<String>) -> Result<View> {
    let (topic, lesson, subject) = find_lesson(&db, &slug).await?;
    let student = student_id(&db, &user).await?;
    let mut state = TopicState::NONE;
    let mut last: Option<LessonCheck> = None;
    if let Some(id) = student {
        state = status::states(&db, id)
            .await?
            .get(&topic.id)
            .copied()
            .unwrap_or(TopicState::NONE);
        last = LessonCheck::query()
            .where_(LessonCheck::USER_ID.eq(id))
            .where_(LessonCheck::TOPIC_ID.eq(topic.id))
            .where_(LessonCheck::SCORE.is_not_null())
            .order_by_desc(LessonCheck::ID)
            .first(&db)
            .await?;
    }
    let parsed = parse_lesson(&lesson.markdown);
    let scheduled = status::scheduled_dates(&db)
        .await?
        .get(&topic.slug)
        .map(|d| d.format("%A %-d %B").to_string());
    let last_attempt = last.as_ref().and_then(|c| {
        c.score.map(|score| Attempt {
            score,
            on: c.checked_on.format("%-d %b").to_string(),
            passed: score >= status::PASS_SCORE,
        })
    });
    Ok(View::typed(ShowPage {
        title: lesson.title.clone(),
        slug: topic.slug.clone(),
        subject_name: subject.name,
        color: subject.color,
        emoji: subject.emoji,
        is_parent: !user.has_role(STUDENT),
        // The page header already shows the title, so the file's own `# Title` line is dropped.
        body_html: render::render_markdown(
            parsed
                .body
                .split_once('\n')
                .filter(|_| parsed.body.starts_with("# "))
                .map_or(parsed.body.as_str(), |(_, rest)| rest),
        ),
        key_html: render::render_markdown(&parsed.key_block),
        watch: lesson
            .watch_links
            .0
            .iter()
            .map(|w| WatchView {
                label: w.label.clone(),
                url: w.url.clone(),
                note: w.note.clone(),
            })
            .collect(),
        questions: question_views(&parsed.questions, last.as_ref()),
        drawn: state.drawn,
        best_score: state.best_score,
        status: state.status,
        status_label: state.status.label(),
        status_icon: state.status.icon(),
        status_kind: state.status.kind(),
        scheduled,
        last_attempt,
        pass_score: status::PASS_SCORE,
    }))
}

// ---------------------------------------------------------------------------------------------
// Saving

#[derive(Deserialize, Validate)]
struct DrawnForm {
    drawn: bool,
}

/// "I redrew it from memory": ticks (or unticks) the mark on every row of the student's topic.
async fn mark_drawn(
    State(db): State<Db>,
    user: AuthUser,
    Path(slug): Path<String>,
    Valid(form): Valid<DrawnForm>,
) -> Result<impl IntoResponse> {
    let (topic, _, _) = find_lesson(&db, &slug).await?;
    renox::db::sql("UPDATE lesson_checks SET drawn = ? WHERE user_id = ? AND topic_id = ?")
        .bind(form.drawn)
        .bind(user.id)
        .bind(topic.id)
        .execute(&db)
        .await?;
    let rows: i64 =
        renox::db::sql("SELECT COUNT(*) FROM lesson_checks WHERE user_id = ? AND topic_id = ?")
            .bind(user.id)
            .bind(topic.id)
            .scalar(&db)
            .await?;
    if form.drawn && rows == 0 {
        LessonCheck::create(
            &db,
            LessonCheck {
                user_id: user.id,
                topic_id: topic.id,
                score: None,
                drawn: true,
                answers: Json(HashMap::new()),
                checked_on: crate::clock::today(),
                ..Default::default()
            },
        )
        .await?;
    }
    let toast = if form.drawn {
        Toast::success("Marked as redrawn from memory.")
    } else {
        Toast::success("Mark removed.")
    };
    Ok((toast, Redirect::route("lessons.show", &[&slug])?))
}

#[derive(Deserialize, Validate)]
struct CheckForm {
    #[serde(default)]
    q1: Option<String>,
    #[serde(default)]
    q2: Option<String>,
    #[serde(default)]
    q3: Option<String>,
    #[serde(default)]
    q4: Option<String>,
    #[serde(default)]
    q5: Option<String>,
}

/// Scores the five answers against the key of the lesson.
pub fn score_answers(questions: &[CheckQuestion], answers: &HashMap<String, String>) -> i64 {
    questions
        .iter()
        .filter(|q| answers.get(&q.number.to_string()) == Some(&q.answer))
        .count() as i64
}

async fn check(
    State(db): State<Db>,
    user: AuthUser,
    Path(slug): Path<String>,
    Valid(form): Valid<CheckForm>,
) -> Result<impl IntoResponse> {
    let (topic, lesson, _) = find_lesson(&db, &slug).await?;
    let parsed = parse_lesson(&lesson.markdown);
    let mut answers = HashMap::new();
    for (number, value) in [form.q1, form.q2, form.q3, form.q4, form.q5]
        .into_iter()
        .enumerate()
    {
        if let Some(letter) = value.map(|v| v.trim().to_ascii_uppercase())
            && ["A", "B", "C", "D", "E"].contains(&letter.as_str())
        {
            answers.insert((number + 1).to_string(), letter);
        }
    }
    let score = score_answers(&parsed.questions, &answers);
    let drawn: Option<i64> =
        renox::db::sql("SELECT MAX(drawn) FROM lesson_checks WHERE user_id = ? AND topic_id = ?")
            .bind(user.id)
            .bind(topic.id)
            .scalar_optional(&db)
            .await?;
    LessonCheck::create(
        &db,
        LessonCheck {
            user_id: user.id,
            topic_id: topic.id,
            score: Some(score),
            drawn: drawn.unwrap_or(0) > 0,
            answers: Json(answers),
            checked_on: crate::clock::today(),
            ..Default::default()
        },
    )
    .await?;
    let toast = if score >= status::PASS_SCORE {
        Toast::success(format!("{score} of 5 right. Well done!"))
    } else {
        Toast::success(format!(
            "{score} of 5 right. Read the explanations, then try again."
        ))
    };
    Ok((toast, Redirect::route("lessons.show", &[&slug])?))
}
