//! Picture-first flashcards with spaced repetition (5-box Leitner).
//!
//! * `/flashcards` is the overview: numbers per subject, the cards the student made, and the
//!   "Start review" button. The parent sees the same numbers, read-only.
//! * `/flashcards/review` is a live component that walks through today's queue.
//! * Manual cards (`origin = manual`) are added, changed and removed by the student or parent.
//!
//! The Today page asks [`due_count`] how many cards are waiting.

pub mod card;
pub mod deck;
pub mod grading;
pub mod leitner;
pub mod models;
pub mod review;
pub mod svg;

use crate::app::content::models::{Flashcard, Subject, Topic};
use crate::app::accounts::{PARENT, STUDENT};
use deck::Deck;
use renox::db::Json;
use renox::prelude::*;
use serde::Deserialize;

pub use deck::due_count;

pub struct Flashcards;

impl Module for Flashcards {
    fn name(&self) -> &'static str {
        "flashcards"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<models::CardState>();
        app.model::<models::CardReview>();
        app.live_component::<review::Review>();
    }

    fn routes(&self) -> Routes {
        // Student and parent: the overview and the cards they made themselves.
        let pages = Routes::new()
            .get("/flashcards", index)
            .name("flashcards.index")
            .get("/flashcards/manual/new", create)
            .name("flashcards.create")
            .get("/flashcards/manual/topics", topics)
            .name("flashcards.topics")
            .post("/flashcards/manual", store)
            .name("flashcards.store")
            .get("/flashcards/manual/{id}/edit", edit)
            .name("flashcards.edit")
            .post("/flashcards/manual/{id}", update)
            .name("flashcards.update")
            .delete("/flashcards/manual/{id}", destroy)
            .name("flashcards.destroy")
            .require_auth();
        // Only the student reviews (the parent gets a 403).
        let student = Routes::new()
            .get("/flashcards/review", review_page)
            .name("flashcards.review")
            .require_role(STUDENT)
            .require_auth();
        pages.merge(student)
    }
}

#[derive(Deserialize, Default)]
struct Filter {
    subject: Option<String>,
}

/// A subject filter that names a subject we know; anything else means "all".
fn known_subject(subjects: &[Subject], wanted: &Option<String>) -> Option<String> {
    wanted
        .as_deref()
        .filter(|w| subjects.iter().any(|s| s.slug == *w))
        .map(str::to_owned)
}

async fn index(
    State(state): State<AppState>,
    user: AuthUser,
    Query(filter): Query<Filter>,
) -> Result<View> {
    let db = &state.db;
    let today = crate::clock::today();
    let can_review = user.has_role(STUDENT);
    let student = deck::student_id(db, &user).await?;
    let mut stats = Vec::new();
    let mut queue_len = 0usize;
    let mut due_total = 0i64;
    let subjects;
    let mut selected = None;
    let mut manual = Vec::new();
    if let Some(student) = student {
        let deck = Deck::load(db, student).await?;
        selected = known_subject(&deck.subjects, &filter.subject);
        let plan = deck::plan_subject(db, today).await?;
        queue_len = deck.queue(today, plan.as_deref(), selected.as_deref()).items.len();
        stats = deck.stats(today);
        due_total = stats.iter().map(|s| s.due).sum();
        subjects = deck.subjects.clone();
        for card in deck
            .cards
            .iter()
            .filter(|c| c.origin == "manual")
            .filter(|c| selected.is_none() || deck.subject_of(c).map(|s| &s.slug) == selected.as_ref())
        {
            let subject = deck.subject_of(card);
            manual.push(json!({
                "id": card.id,
                "front": card.front,
                "type": card.card_type,
                "has_image": card.visual.is_some(),
                "color": subject.map(|s| s.color.clone()),
                "subject": subject.map(|s| s.name.clone()),
                "slug": subject.map(|s| s.slug.clone()),
            }));
        }
    } else {
        subjects = Subject::query().order_by(Subject::POSITION).get(db).await?;
    }
    let visible: Vec<_> = stats
        .iter()
        .filter(|s| selected.as_ref().is_none_or(|slug| *slug == s.slug))
        .collect();

    // One series per box, so the bars show how far each subject has come.
    let series: Vec<_> = (0..5)
        .map(|b| {
            json!({
                "name": format!("Box {}", b + 1),
                "values": visible.iter().map(|s| s.boxes[b]).collect::<Vec<_>>(),
            })
        })
        .collect();
    let labels: Vec<_> = visible.iter().map(|s| s.name.clone()).collect();
    let started: i64 = visible.iter().map(|s| s.boxes.iter().sum::<i64>()).sum();
    Ok(view(
        "flashcards/index.html",
        context! {
            title => "Flashcards",
            stats => visible,
            labels,
            series,
            started,
            subjects,
            selected,
            queue_len,
            due_total,
            can_review,
            manual,
            has_student => student.is_some(),
            is_parent => user.has_role(PARENT),
        },
    ))
}

async fn review_page(
    State(_state): State<AppState>,
    user: AuthUser,
    ctx: renox::live_component::LiveContext,
    Query(filter): Query<Filter>,
) -> Result<View> {
    let db = &ctx.state().db;
    let subjects = Subject::query().get(db).await?;
    let only = known_subject(&subjects, &filter.subject);
    let session = review::new_session(db, user.id, crate::clock::today(), only.as_deref()).await?;
    let review = ctx.mount(session).await?;
    Ok(view(
        "flashcards/review.html",
        context! { title => "Review", review },
    ))
}

// ----- Manual cards ---------------------------------------------------------------------

#[derive(Deserialize, Validate)]
struct CardForm {
    #[validate(required)]
    topic: Option<i64>,
    #[validate(required, max = 300)]
    front: String,
    #[validate(required, max = 600)]
    back: String,
    #[validate(max = 400)]
    sketch_prompt: Option<String>,
    #[validate(mimes(&["png", "jpg", "jpeg", "svg"]), max = 2048)]
    image: Option<Upload>,
    /// Only used to fill the subtopic list; not stored.
    #[serde(default)]
    #[allow(dead_code)]
    subject: Option<String>,
    #[serde(default)]
    remove_image: Option<bool>,
}

async fn subject_options(db: &Db) -> Result<Vec<Vec<String>>> {
    Ok(Subject::query()
        .order_by(Subject::POSITION)
        .get(db)
        .await?
        .into_iter()
        .map(|s| vec![s.slug, format!("{} {}", s.emoji, s.name)])
        .collect())
}

/// The subtopics of one subject, as `[id, name]` options for a select.
async fn topic_options(db: &Db, subject_slug: &str) -> Result<Vec<Vec<String>>> {
    let Some(subject) = Subject::query()
        .where_(Subject::SLUG.eq(subject_slug))
        .first(db)
        .await?
    else {
        return Ok(vec![]);
    };
    Ok(Topic::query()
        .where_(Topic::SUBJECT_ID.eq(subject.id))
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::POSITION)
        .get(db)
        .await?
        .into_iter()
        .map(|t| vec![t.id.to_string(), t.name])
        .collect())
}

async fn form_page(
    state: &AppState,
    card: Option<&Flashcard>,
    subject: Option<String>,
) -> Result<View> {
    let db = &state.db;
    let mut subject = subject;
    let mut topic = None;
    if let Some(card) = card
        && let Some(t) = Topic::find(db, card.topic_id).await?
    {
        topic = Some(t.id.to_string());
        if let Some(s) = Subject::find(db, t.subject_id).await? {
            subject = Some(s.slug);
        }
    }
    let subjects = subject_options(db).await?;
    let topics = match &subject {
        Some(slug) => topic_options(db, slug).await?,
        None => vec![],
    };
    Ok(view(
        "flashcards/form.html",
        context! {
            title => if card.is_some() { "Edit card" } else { "New card" },
            card,
            subject_options => subjects,
            topic_options => topics,
            subject,
            topic,
        },
    ))
}

async fn create(State(state): State<AppState>) -> Result<View> {
    form_page(&state, None, None).await
}

async fn edit(State(state): State<AppState>, Found(card): Found<Flashcard>) -> Result<View> {
    ensure_manual(&card)?;
    form_page(&state, Some(&card), None).await
}

/// The subtopic select for the chosen subject (htmx, when the subject select changes).
async fn topics(State(state): State<AppState>, Query(filter): Query<Filter>) -> Result<View> {
    let options = match &filter.subject {
        Some(slug) => topic_options(&state.db, slug).await?,
        None => vec![],
    };
    Ok(view(
        "flashcards/_topic_select.html",
        context! { topic_options => options, topic => Option::<String>::None },
    ))
}

fn ensure_manual(card: &Flashcard) -> Result {
    if card.origin != "manual" || card.archived_at.is_some() {
        return Err(Error::NotFound);
    }
    Ok(())
}

/// The subtopic must exist and be a subtopic (cards hang on subtopics).
async fn check_topic(db: &Db, topic: i64) -> Result<Topic> {
    let found = Topic::find(db, topic).await?;
    match found {
        Some(t) if t.parent_id.is_some() => Ok(t),
        _ => {
            let mut errors = Errors::new();
            errors.add("topic", "Pick a subtopic from the list.");
            Err(ValidationError::new(errors).into())
        }
    }
}

fn no_picture() -> Error {
    let mut errors = Errors::new();
    errors.add(
        "sketch_prompt",
        "Add a picture, or write what to draw on paper.",
    );
    ValidationError::new(errors).into()
}

fn clean(text: Option<String>) -> Option<String> {
    text.map(|t| t.trim().to_owned()).filter(|t| !t.is_empty())
}

async fn store(
    State(state): State<AppState>,
    Valid(form): Valid<CardForm>,
) -> Result<(Toast, Redirect)> {
    let db = &state.db;
    let topic = check_topic(db, form.topic.unwrap_or_default()).await?;
    let sketch = clean(form.sketch_prompt);
    if form.image.is_none() && sketch.is_none() {
        return Err(no_picture());
    }
    let visual = match &form.image {
        Some(image) => {
            let key = image.store_public(&state.storage, "flashcards").await?;
            Some(state.storage.url(&key))
        }
        None => None,
    };
    Flashcard::create(
        db,
        Flashcard {
            key: format!("manual-{}", &renox::random_token()[..12]),
            topic_id: topic.id,
            card_type: card::BASIC.to_owned(),
            front: form.front.trim().to_owned(),
            back: form.back.trim().to_owned(),
            visual,
            sketch_prompt: sketch,
            payload: Json(json!({})),
            tags: Json(vec![]),
            origin: "manual".to_owned(),
            ..Default::default()
        },
    )
    .await?;
    Ok((Toast::success("Card added."), Redirect::to("/flashcards")))
}

async fn update(
    State(state): State<AppState>,
    Found(mut card): Found<Flashcard>,
    Valid(form): Valid<CardForm>,
) -> Result<(Toast, Redirect)> {
    ensure_manual(&card)?;
    let db = &state.db;
    let topic = check_topic(db, form.topic.unwrap_or_default()).await?;
    let sketch = clean(form.sketch_prompt);
    let old_visual = card.visual.clone();
    let mut visual = old_visual.clone();
    if let Some(image) = &form.image {
        let key = image.store_public(&state.storage, "flashcards").await?;
        visual = Some(state.storage.url(&key));
    } else if form.remove_image == Some(true) {
        visual = None;
    }
    if visual.is_none() && sketch.is_none() {
        return Err(no_picture());
    }
    card.topic_id = topic.id;
    card.front = form.front.trim().to_owned();
    card.back = form.back.trim().to_owned();
    card.sketch_prompt = sketch;
    card.visual = visual.clone();
    card.save(db).await?;
    if old_visual != visual {
        delete_upload(&state, old_visual.as_deref()).await;
    }
    Ok((Toast::success("Card saved."), Redirect::to("/flashcards")))
}

async fn destroy(
    State(state): State<AppState>,
    Found(mut card): Found<Flashcard>,
) -> Result<(Toast, Redirect)> {
    ensure_manual(&card)?;
    card.delete(&state.db).await?;
    delete_upload(&state, card.visual.as_deref()).await;
    Ok((Toast::success("Card deleted."), Redirect::to("/flashcards")))
}

/// Removes an uploaded picture from the public disk. Content pictures are never touched.
async fn delete_upload(state: &AppState, visual: Option<&str>) {
    if let Some(rest) = visual.and_then(|v| v.strip_prefix("/storage/")) {
        let _ = state.storage.delete(&format!("public/{rest}")).await;
    }
}
