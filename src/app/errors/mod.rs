//! The Error Log: every mistake becomes study material. Wrong and guessed answers of finished
//! practice attempts are logged automatically ([`record::record_attempt`]); paper questions are
//! added by hand with a sketch photo. Entries are repeated on a Leitner schedule until resolved.
//!
//! The student writes; the parent sees the same list read-only. Photos are private files: they
//! are served by `errors.image`, never from `public/`.

pub mod leitner;
pub mod models;
pub mod record;
pub mod stats;

use crate::app::content::models::{Question, Subject, Topic};
use crate::app::practice::engine::student_user_id;
use leitner::Grade;
use models::{CAUSES, ErrorEntry, OPEN, ORIGIN_MANUAL, RESOLVED, cause_label, is_cause};
use renox::grid::{Column, Grid, GridRequest};
use renox::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const STUDENT: &str = "student";
pub const PARENT: &str = "parent";

pub struct Errors;

impl Module for Errors {
    fn name(&self) -> &'static str {
        "errors"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<ErrorEntry>();
    }

    fn routes(&self) -> Routes {
        // Student and parent: the list, one entry and its photo (the parent only reads).
        let shared = Routes::new()
            .get("/errors", index)
            .name("errors.index")
            .get("/errors/{id}", show)
            .name("errors.show")
            .get("/errors/{id}/image", image)
            .name("errors.image")
            .require_auth();
        // Only the student adds, changes, reviews and resolves.
        let student = Routes::new()
            .get("/errors/new", new)
            .name("errors.new")
            .post("/errors", store)
            .name("errors.store")
            .get("/errors/review", review)
            .name("errors.review")
            .post("/errors/review/cause", review_cause)
            .name("errors.review_cause")
            .post("/errors/{id}/rate", rate)
            .name("errors.rate")
            .put("/errors/{id}/cause", set_cause)
            .name("errors.cause")
            .post("/errors/{id}/photo", set_photo)
            .name("errors.photo")
            .post("/errors/{id}/resolve", resolve)
            .name("errors.resolve")
            .require_role(STUDENT);
        shared.merge(student)
    }
}

// ---- Access ------------------------------------------------------------------------------

fn is_parent(user: &User) -> bool {
    user.has_role(PARENT)
}

/// Whose entries this user sees: their own, or (for the parent) the student's.
async fn owner_id(db: &Db, user: &User) -> Result<Option<i64>> {
    if is_parent(user) {
        student_user_id(db).await
    } else {
        Ok(Some(user.id))
    }
}

/// An entry the user may look at (own, or the student's for the parent).
async fn readable(db: &Db, user: &User, id: i64) -> Result<ErrorEntry> {
    let entry = ErrorEntry::find_or_404(db, id).await?;
    match owner_id(db, user).await? {
        Some(owner) if owner == entry.user_id => Ok(entry),
        _ => Err(Error::NotFound),
    }
}

/// An entry the student may change: always their own.
async fn own(db: &Db, user: &User, id: i64) -> Result<ErrorEntry> {
    let entry = ErrorEntry::find_or_404(db, id).await?;
    if entry.user_id == user.id {
        Ok(entry)
    } else {
        Err(Error::NotFound)
    }
}

fn cause_options() -> Vec<(&'static str, &'static str)> {
    CAUSES.iter().map(|(v, l, _)| (*v, *l)).collect()
}

// ---- The list --------------------------------------------------------------------------

fn errors_grid() -> Grid {
    let subjects: Vec<(&str, &str)> = vec![
        ("math", "Mathematics"),
        ("physics", "Physics"),
        ("chemistry", "Chemistry"),
        ("biology", "Biology"),
        ("earth", "Earth Science"),
    ];
    Grid::new("errors")
        .title("Mistakes")
        .per_page(25)
        .column(Column::custom("dot", "").mobile())
        .column(Column::select("subject", "Subject", subjects).mobile())
        .column(Column::custom("topic", "Subtopic").mobile())
        .column(Column::custom("what", "Question"))
        .column(
            Column::select("cause", "Cause", cause_options())
                .badges(&[
                    ("concept", "danger"),
                    ("calculation", "warning"),
                    ("misread", "info"),
                    ("rushed", "warning"),
                    ("guess", "neutral"),
                ])
                .mobile(),
        )
        .column(
            Column::select("status", "Status", [(OPEN, "Open"), (RESOLVED, "Resolved")])
                .badges(&[(OPEN, "warning"), (RESOLVED, "success")]),
        )
        .column(Column::date("due_on", "Due").mobile())
        .column(Column::number("box_no", "Box"))
        .column(Column::custom("photo", "Sketch").width("6rem"))
        .column(Column::custom("actions", "").frozen_right())
        .sort_by("due_on,id")
}

#[derive(Serialize)]
struct TopRow {
    name: String,
    subject: String,
    color: String,
    count: i64,
    /// 0..=100 for the bar.
    width: i64,
}

async fn index(
    State(state): State<AppState>,
    user: AuthUser,
    request: GridRequest,
) -> Result<View> {
    let db = &state.db;
    let parent = is_parent(&user);
    let owner = owner_id(db, &user).await?.unwrap_or(0);

    let query = ErrorEntry::query().where_(ErrorEntry::USER_ID.eq(owner));
    let page = errors_grid().page(query, &request).await?;

    // What each row needs from other tables: 3 queries for the page.
    let topic_ids: Vec<i64> = page.items().iter().map(|e| e.topic_id).collect();
    let question_ids: Vec<i64> = page.items().iter().filter_map(|e| e.question_id).collect();
    let topics: HashMap<i64, Topic> = Topic::find_many(db, topic_ids)
        .await?
        .into_iter()
        .map(|t| (t.id, t))
        .collect();
    let questions: HashMap<i64, Question> = Question::find_many(db, question_ids)
        .await?
        .into_iter()
        .map(|q| (q.id, q))
        .collect();
    let subjects: HashMap<String, Subject> = Subject::query()
        .get(db)
        .await?
        .into_iter()
        .map(|s| (s.slug.clone(), s))
        .collect();
    let today = crate::clock::today();
    let page = page.extend(|e| {
        let subject = subjects.get(&e.subject);
        let what = match (questions.get(&e.question_id.unwrap_or(0)), &e.source) {
            (Some(q), _) => truncate(&q.stem, 70),
            (None, Some(source)) => match &e.question_no {
                Some(no) => format!("{source}, question {no}"),
                None => source.clone(),
            },
            _ => e
                .note
                .as_deref()
                .map(|n| truncate(n, 70))
                .unwrap_or_default(),
        };
        json!({
            "color": subject.map(|s| s.color.clone()).unwrap_or_default(),
            "subject_name": subject.map(|s| s.name.clone()).unwrap_or_default(),
            "topic_name": topics.get(&e.topic_id).map(|t| t.name.clone()).unwrap_or_default(),
            "what": what,
            "is_open": e.status == OPEN,
            "is_due": e.status == OPEN && e.due_on <= today,
            "cause_label": e.cause.as_deref().map_or("Not set", cause_label),
        })
    });

    let causes = stats::cause_counts(db, owner).await?;
    let top = stats::top_subtopics(db, owner, 10).await?;
    let most = top.first().map_or(1, |t| t.count).max(1);
    let top: Vec<TopRow> = top
        .into_iter()
        .map(|t| TopRow {
            width: (t.count * 100 / most).max(4),
            name: t.name,
            subject: t.subject_name,
            color: t.color,
            count: t.count,
        })
        .collect();
    let cause_labels: Vec<&str> = causes.iter().map(|(c, _)| cause_label(c)).collect();
    let cause_values: Vec<i64> = causes.iter().map(|(_, n)| *n).collect();
    let total: i64 = cause_values.iter().sum();
    let due = stats::due_count(db, owner, today).await?;
    let redo = stats::redo_count(db, owner, today).await?;

    Ok(view(
        "errors/index.html",
        context! {
            title => "Error Log",
            entries => page,
            is_parent => parent,
            cause_options => cause_options(),
            cause_labels,
            cause_values,
            top,
            total,
            due,
            redo,
        },
    ))
}

fn truncate(text: &str, max: usize) -> String {
    let text = text.trim();
    if text.chars().count() <= max {
        text.to_owned()
    } else {
        let cut: String = text.chars().take(max).collect();
        format!("{}…", cut.trim_end())
    }
}

// ---- One entry --------------------------------------------------------------------------

async fn show(State(state): State<AppState>, user: AuthUser, Path(id): Path<i64>) -> Result<View> {
    let db = &state.db;
    let entry = readable(db, &user, id).await?;
    let topic = Topic::find_or_404(db, entry.topic_id).await?;
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    let question = match entry.question_id {
        Some(qid) => Question::find(db, qid).await?,
        None => None,
    };
    let today = crate::clock::today();
    Ok(view(
        "errors/show.html",
        context! {
            title => "Mistake",
            is_parent => is_parent(&user),
            cause_label => entry.cause.as_deref().map_or("Not set", cause_label),
            cause_options => cause_options(),
            is_open => entry.status == OPEN,
            is_due => entry.status == OPEN && entry.due_on <= today,
            entry,
            topic,
            subject,
            question,
        },
    ))
}

async fn image(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
) -> Result<Response> {
    let entry = readable(&state.db, &user, id).await?;
    let key = entry.photo.ok_or(Error::NotFound)?;
    let bytes = state.storage.get(&key).await?.ok_or(Error::NotFound)?;
    let content_type = match key.rsplit('.').next() {
        Some("jpg") | Some("jpeg") => "image/jpeg",
        Some("gif") => "image/gif",
        Some("webp") => "image/webp",
        _ => "image/png",
    };
    Ok((
        [
            (renox::axum::http::header::CONTENT_TYPE, content_type),
            (
                renox::axum::http::header::CACHE_CONTROL,
                "private, max-age=3600",
            ),
            (renox::axum::http::header::X_CONTENT_TYPE_OPTIONS, "nosniff"),
        ],
        bytes,
    )
        .into_response())
}

// ---- Add a mistake by hand --------------------------------------------------------------

/// Titles of the past papers in `content/sources.json`.
fn source_titles() -> Vec<String> {
    const SOURCES: &str = include_str!("../../../content/sources.json");
    let json: renox::serde_json::Value = renox::serde_json::from_str(SOURCES).unwrap_or_default();
    json["past_papers"]
        .as_array()
        .map(|papers| {
            papers
                .iter()
                .filter_map(|p| p["title"].as_str().map(str::to_owned))
                .collect()
        })
        .unwrap_or_default()
}

async fn subtopic_options(db: &Db) -> Result<Vec<(String, String)>> {
    let subjects = Subject::query().order_by(Subject::POSITION).get(db).await?;
    let subtopics = Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::POSITION)
        .get(db)
        .await?;
    let mut options = Vec::new();
    for s in &subjects {
        for t in subtopics.iter().filter(|t| t.subject_id == s.id) {
            options.push((t.id.to_string(), format!("{} · {}", s.name, t.name)));
        }
    }
    Ok(options)
}

async fn new(State(state): State<AppState>) -> Result<View> {
    let sources: Vec<(String, String)> = source_titles()
        .into_iter()
        .map(|t| (t.clone(), t))
        .collect();
    Ok(view(
        "errors/new.html",
        context! {
            title => "Add a mistake",
            subtopics => subtopic_options(&state.db).await?,
            sources,
            cause_options => cause_options(),
        },
    ))
}

#[derive(Deserialize)]
struct NewForm {
    topic: Option<i64>,
    source: Option<String>,
    source_other: Option<String>,
    question_no: Option<String>,
    cause: Option<String>,
    note: Option<String>,
    photo: Option<Upload>,
}

impl Validate for NewForm {
    fn rules(&self, v: &mut Validator) {
        v.field("topic", &self.topic).required();
        v.field("cause", &self.cause).required();
        v.field("source", &self.source).max(200);
        v.field("source_other", &self.source_other).max(200);
        v.field("question_no", &self.question_no).max(40);
        v.field("note", &self.note).max(2000);
        v.field("photo", &self.photo).image().max(5120); // KB
        if clean(&self.note).is_none() && self.photo.is_none() {
            v.error("note", "Write a note or add a sketch photo (at least one).");
        }
    }
}

fn clean(value: &Option<String>) -> Option<String> {
    value
        .as_deref()
        .map(str::trim)
        .filter(|v| !v.is_empty())
        .map(str::to_owned)
}

async fn store(
    State(state): State<AppState>,
    user: AuthUser,
    Valid(form): Valid<NewForm>,
) -> Result<impl IntoResponse> {
    let db = &state.db;
    let topic = Topic::find_or_404(db, form.topic.unwrap_or(0)).await?;
    if topic.parent_id.is_none() {
        return Err(abort(
            StatusCode::UNPROCESSABLE_ENTITY,
            "Pick a subtopic, not a whole topic.",
        ));
    }
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    let cause = form.cause.clone().filter(|c| is_cause(c));
    if cause.is_none() {
        return Err(abort(StatusCode::UNPROCESSABLE_ENTITY, "Pick a cause."));
    }
    let photo = match &form.photo {
        Some(upload) => Some(upload.store(&state.storage, "errors").await?),
        None => None,
    };
    let entry = ErrorEntry::create(
        db,
        ErrorEntry {
            user_id: user.id,
            origin: ORIGIN_MANUAL.into(),
            topic_id: topic.id,
            subject: subject.slug,
            source: clean(&form.source_other).or_else(|| clean(&form.source)),
            question_no: clean(&form.question_no),
            cause,
            note: clean(&form.note),
            photo,
            box_no: 1,
            due_on: leitner::due_on(crate::clock::today(), 1),
            status: OPEN.into(),
            ..Default::default()
        },
    )
    .await?;
    Ok((
        Toast::success("Mistake added. It will come back for review tomorrow."),
        Redirect::route("errors.show", &[&entry.id])?,
    ))
}

// ---- Change an entry ----------------------------------------------------------------------

#[derive(Deserialize, Validate)]
struct CauseForm {
    #[validate(required)]
    cause: Option<String>,
}

fn valid_cause(form: &CauseForm) -> Result<String> {
    form.cause
        .clone()
        .filter(|c| is_cause(c))
        .ok_or_else(|| abort(StatusCode::UNPROCESSABLE_ENTITY, "Pick a cause."))
}

async fn set_cause(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
    Valid(form): Valid<CauseForm>,
) -> Result<impl IntoResponse> {
    let mut entry = own(&state.db, &user, id).await?;
    entry.cause = Some(valid_cause(&form)?);
    entry.save(&state.db).await?;
    Ok((Toast::success("Cause saved."), HxRefresh))
}

#[derive(Deserialize, Validate)]
struct ReviewCauseForm {
    #[validate(required)]
    id: Option<i64>,
    #[validate(required)]
    cause: Option<String>,
}

/// The cause prompt at the start of a review.
async fn review_cause(
    State(state): State<AppState>,
    user: AuthUser,
    Valid(form): Valid<ReviewCauseForm>,
) -> Result<impl IntoResponse> {
    let mut entry = own(&state.db, &user, form.id.unwrap_or(0)).await?;
    entry.cause = Some(valid_cause(&CauseForm { cause: form.cause })?);
    entry.save(&state.db).await?;
    Redirect::route("errors.review", &[])
}

#[derive(Deserialize)]
struct PhotoForm {
    photo: Upload,
}

impl Validate for PhotoForm {
    fn rules(&self, v: &mut Validator) {
        v.field("photo", &self.photo).required().image().max(5120); // KB
    }
}

async fn set_photo(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
    Valid(form): Valid<PhotoForm>,
) -> Result<impl IntoResponse> {
    let mut entry = own(&state.db, &user, id).await?;
    let key = form.photo.store(&state.storage, "errors").await?;
    if let Some(old) = entry.photo.replace(key) {
        let _ = state.storage.delete(&old).await;
    }
    entry.save(&state.db).await?;
    Ok((
        Toast::success("Sketch saved."),
        Redirect::route("errors.show", &[&id])?,
    ))
}

async fn resolve(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
) -> Result<impl IntoResponse> {
    let mut entry = own(&state.db, &user, id).await?;
    if entry.status == OPEN {
        entry.status = RESOLVED.into();
        entry.resolved_at = Some(renox::db::now());
        entry.save(&state.db).await?;
    }
    Ok((Toast::success("Marked as resolved."), HxRefresh))
}

// ---- Review -------------------------------------------------------------------------------

#[derive(Serialize)]
struct ChoiceView {
    letter: &'static str,
    text: String,
    /// `correct`, `wrong` or empty.
    state: &'static str,
    href: String,
}

#[derive(Deserialize, Default)]
struct ReviewQuery {
    pick: Option<String>,
    reveal: Option<String>,
}

async fn review(
    State(state): State<AppState>,
    user: AuthUser,
    Query(query): Query<ReviewQuery>,
) -> Result<View> {
    let db = &state.db;
    let today = crate::clock::today();
    let due = stats::due_entries(db, user.id, today).await?;
    let Some(entry) = due.first().cloned() else {
        let next = stats::next_due(db, user.id).await?;
        return Ok(view(
            "errors/review.html",
            context! { title => "Review mistakes", done => true, next_due => next },
        ));
    };
    let topic = Topic::find_or_404(db, entry.topic_id).await?;
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    let question = match entry.question_id {
        Some(qid) => Question::find(db, qid).await?,
        None => None,
    };
    let picked = query.pick.as_deref().map(str::to_uppercase).filter(|p| {
        question
            .as_ref()
            .is_some_and(|q| q.choices().iter().any(|(l, _)| l == p))
    });
    let reveal = picked.is_some() || query.reveal.is_some();
    let choices: Vec<ChoiceView> = question
        .as_ref()
        .map(|q| {
            q.choices()
                .iter()
                .map(|(letter, text)| {
                    let is_key = *letter == q.answer;
                    let is_pick = picked.as_deref() == Some(*letter);
                    ChoiceView {
                        letter,
                        text: (*text).to_owned(),
                        state: if reveal && is_key {
                            "correct"
                        } else if reveal && is_pick {
                            "wrong"
                        } else {
                            ""
                        },
                        href: format!("{}?pick={letter}", "/errors/review"),
                    }
                })
                .collect()
        })
        .unwrap_or_default();
    let was_right = match (&picked, &question) {
        (Some(p), Some(q)) => Some(*p == q.answer),
        _ => None,
    };
    Ok(view(
        "errors/review.html",
        context! {
            title => "Review mistakes",
            done => false,
            remaining => due.len(),
            needs_cause => !entry.has_cause(),
            cause_label => entry.cause.as_deref().map_or("Not set", cause_label),
            causes => CAUSES.iter().map(|(v, l, h)| json!({"value": v, "label": l, "hint": h})).collect::<Vec<_>>(),
            reveal,
            choices,
            was_right,
            entry,
            topic,
            subject,
            question,
        },
    ))
}

#[derive(Deserialize, Validate)]
struct RateForm {
    #[validate(required)]
    grade: Option<String>,
}

async fn rate(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
    Valid(form): Valid<RateForm>,
) -> Result<impl IntoResponse> {
    let db = &state.db;
    let mut entry = own(db, &user, id).await?;
    let grade = form
        .grade
        .as_deref()
        .and_then(Grade::parse)
        .ok_or_else(|| abort(StatusCode::UNPROCESSABLE_ENTITY, "Unknown grade."))?;
    abort_if(
        entry.status != OPEN,
        StatusCode::UNPROCESSABLE_ENTITY,
        "This mistake is already resolved.",
    )?;
    abort_if(
        !entry.has_cause(),
        StatusCode::UNPROCESSABLE_ENTITY,
        "Choose the cause of this mistake first.",
    )?;
    let next = leitner::apply(entry.box_no, grade);
    entry.box_no = next.box_no;
    entry.reviews += 1;
    entry.last_grade = Some(grade.as_str().to_owned());
    if next.resolved {
        entry.status = RESOLVED.into();
        entry.resolved_at = Some(renox::db::now());
    } else {
        entry.due_on = leitner::due_on(crate::clock::today(), next.box_no);
    }
    entry.save(db).await?;
    let toast = if next.resolved {
        Toast::success("Resolved! You have mastered this mistake.")
    } else {
        Toast::info(format!(
            "Back in {} day(s).",
            leitner::interval_days(next.box_no)
        ))
    };
    Ok((toast, Redirect::route("errors.review", &[])?))
}
