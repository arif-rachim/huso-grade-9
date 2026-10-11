//! "Redraw from memory" (visual blurting): the student draws a subtopic on a canvas (or uploads a
//! photo of a paper drawing), saves it, and compares it with the reference pictures.
//!
//! The student draws and saves; the parent sees the same drawings read-only.
//! The images are private files: they are served by `canvas.image`, never from `public/`.

use crate::app::content::models::{Flashcard, Subject, Topic};
use renox::chrono::Duration as ChronoDuration;
use renox::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const STUDENT: &str = "student";
pub const PARENT: &str = "parent";

pub struct Canvas;

#[derive(Model, Serialize, Default, Debug, Clone)]
#[model(table = "drawings")]
pub struct Drawing {
    pub id: i64,
    pub user_id: i64,
    pub topic_id: i64,
    /// Key of the private file in storage (`drawings/<random>.png`).
    pub image_path: String,
    pub notes: Option<String>,
    pub created_at: Option<DateTime>,
    pub updated_at: Option<DateTime>,
}

impl Module for Canvas {
    fn name(&self) -> &'static str {
        "canvas"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<Drawing>();
    }

    fn routes(&self) -> Routes {
        // Student and parent: the gallery, a drawing and its image (the parent only reads).
        let shared = Routes::new()
            .get("/redraw", index)
            .name("canvas.index")
            .get("/redraw/drawings/{id}", drawing)
            .name("canvas.drawing")
            .get("/redraw/drawings/{id}/image", image)
            .name("canvas.image")
            .require_auth();
        // Only the student draws and saves.
        let student = Routes::new()
            .get("/redraw/{slug}", draw)
            .name("canvas.show")
            .post("/redraw/{slug}", store)
            .name("canvas.store")
            .require_role(STUDENT);
        shared.merge(student)
    }
}

/// Whose drawings this user sees: their own, or (for the parent) the student's.
async fn owner_id(db: &Db, user: &AuthUser) -> Result<Option<i64>> {
    if user.has_role(PARENT) {
        let id: Option<i64> = renox::db::sql(
            "SELECT u.id FROM users u \
             JOIN role_user ru ON ru.user_id = u.id \
             JOIN roles r ON r.id = ru.role_id \
             WHERE r.name = ? ORDER BY u.id LIMIT 1",
        )
        .bind(STUDENT)
        .scalar_optional(db)
        .await?;
        Ok(id)
    } else {
        Ok(Some(user.id))
    }
}

/// "11 Oct 2026, 14:30" in Jakarta time.
fn jakarta(at: Option<DateTime>) -> String {
    at.map(|t| {
        (t + ChronoDuration::hours(7))
            .format("%-d %b %Y, %H:%M")
            .to_string()
    })
    .unwrap_or_default()
}

#[derive(Serialize)]
struct Card {
    id: i64,
    topic: String,
    topic_slug: String,
    subject: String,
    color: String,
    when: String,
    notes: Option<String>,
}

async fn cards(db: &Db, drawings: Vec<Drawing>) -> Result<Vec<Card>> {
    let topic_ids: Vec<i64> = drawings.iter().map(|d| d.topic_id).collect();
    let topics: HashMap<i64, Topic> = Topic::query()
        .where_(Topic::ID.is_in(topic_ids))
        .get(db)
        .await?
        .into_iter()
        .map(|t| (t.id, t))
        .collect();
    let subjects: HashMap<i64, Subject> = Subject::query()
        .get(db)
        .await?
        .into_iter()
        .map(|s| (s.id, s))
        .collect();
    Ok(drawings
        .into_iter()
        .filter_map(|d| {
            let topic = topics.get(&d.topic_id)?;
            let subject = subjects.get(&topic.subject_id)?;
            Some(Card {
                id: d.id,
                topic: topic.name.clone(),
                topic_slug: topic.slug.clone(),
                subject: subject.name.clone(),
                color: subject.color.clone(),
                when: jakarta(d.created_at),
                notes: d.notes,
            })
        })
        .collect())
}

#[derive(Serialize)]
struct SubtopicLink {
    slug: String,
    name: String,
}

#[derive(Serialize)]
struct SubjectGroup {
    name: String,
    color: String,
    emoji: String,
    subtopics: Vec<SubtopicLink>,
}

async fn index(State(state): State<AppState>, user: AuthUser) -> Result<View> {
    let db = &state.db;
    let is_parent = user.has_role(PARENT);
    let drawings = match owner_id(db, &user).await? {
        Some(owner) => {
            Drawing::query()
                .where_(Drawing::USER_ID.eq(owner))
                .latest()
                .get(db)
                .await?
        }
        None => Vec::new(),
    };
    let gallery = cards(db, drawings).await?;

    // The student picks a subtopic to redraw, grouped by subject.
    let mut groups = Vec::new();
    if !is_parent {
        let subjects = Subject::query().order_by(Subject::POSITION).get(db).await?;
        let subtopics = Topic::query()
            .where_(Topic::PARENT_ID.is_not_null())
            .order_by(Topic::POSITION)
            .get(db)
            .await?;
        for s in subjects {
            let subtopics: Vec<SubtopicLink> = subtopics
                .iter()
                .filter(|t| t.subject_id == s.id)
                .map(|t| SubtopicLink {
                    slug: t.slug.clone(),
                    name: t.name.clone(),
                })
                .collect();
            if !subtopics.is_empty() {
                groups.push(SubjectGroup {
                    name: s.name,
                    color: s.color,
                    emoji: s.emoji,
                    subtopics,
                });
            }
        }
    }
    let (subtitle, empty_message) = if is_parent {
        (
            "The student's drawings (read-only)",
            "The student has not saved a drawing yet.",
        )
    } else {
        (
            "Draw a topic from memory, then compare it with the reference.",
            "Pick a subtopic below and draw it from memory.",
        )
    };
    Ok(view(
        "canvas/index.html",
        context! { title => "Redraw from memory", subtitle, empty_message, gallery, groups, is_parent },
    ))
}

/// The reference pictures of a subtopic: the SVGs of its flashcards, each once.
async fn references(db: &Db, topic: &Topic) -> Result<Vec<String>> {
    let cards = Flashcard::query()
        .where_(Flashcard::TOPIC_ID.eq(topic.id))
        .where_(Flashcard::ARCHIVED_AT.is_null())
        .where_(Flashcard::VISUAL.is_not_null())
        .order_by(Flashcard::ID)
        .get(db)
        .await?;
    let mut seen: Vec<String> = Vec::new();
    for visual in cards.into_iter().filter_map(|c| c.visual) {
        if !visual.is_empty() && !seen.contains(&visual) {
            seen.push(visual);
        }
    }
    Ok(seen)
}

async fn find_subtopic(db: &Db, slug: &str) -> Result<(Topic, Subject)> {
    let topic = Topic::query()
        .where_(Topic::SLUG.eq(slug))
        .where_(Topic::PARENT_ID.is_not_null())
        .first_or_404(db)
        .await?;
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    Ok((topic, subject))
}

/// The page where the student draws.
async fn draw(State(state): State<AppState>, Path(slug): Path<String>) -> Result<View> {
    let (topic, subject) = find_subtopic(&state.db, &slug).await?;
    let all = Subject::query()
        .order_by(Subject::POSITION)
        .get(&state.db)
        .await?;
    let colors: Vec<(String, String)> = all.into_iter().map(|s| (s.name, s.color)).collect();
    Ok(view(
        "canvas/draw.html",
        context! { title => "Redraw from memory", topic, subject, colors },
    ))
}

#[derive(Deserialize)]
struct DrawingForm {
    image: Upload,
    notes: Option<String>,
}

impl Validate for DrawingForm {
    fn rules(&self, v: &mut Validator) {
        v.field("image", &self.image).required().image().max(5120); // KB
        v.field("notes", &self.notes).max(500);
    }
}

async fn store(
    State(state): State<AppState>,
    user: AuthUser,
    Path(slug): Path<String>,
    Valid(form): Valid<DrawingForm>,
) -> Result<impl IntoResponse> {
    let (topic, _) = find_subtopic(&state.db, &slug).await?;
    let key = form.image.store(&state.storage, "drawings").await?;
    let notes = form
        .notes
        .map(|n| n.trim().to_owned())
        .filter(|n| !n.is_empty());
    let saved = Drawing::create(
        &state.db,
        Drawing {
            user_id: user.id,
            topic_id: topic.id,
            image_path: key,
            notes,
            ..Default::default()
        },
    )
    .await?;
    Ok((
        Toast::success("Drawing saved. Now compare it with the reference."),
        Redirect::route("canvas.drawing", &[&saved.id])?,
    ))
}

/// A drawing next to the reference pictures and the syllabus points.
async fn drawing(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
) -> Result<View> {
    let db = &state.db;
    let found = visible_drawing(db, &user, id).await?;
    let topic = Topic::find_or_404(db, found.topic_id).await?;
    let subject = Subject::find_or_404(db, topic.subject_id).await?;
    let references = references(db, &topic).await?;
    let when = jakarta(found.created_at);
    let is_parent = user.has_role(PARENT);
    Ok(view(
        "canvas/drawing.html",
        context! {
            title => "Redraw from memory",
            drawing => found,
            when,
            topic,
            subject,
            references,
            is_parent,
        },
    ))
}

/// The drawing, only when it belongs to the student whose data this user may see.
async fn visible_drawing(db: &Db, user: &AuthUser, id: i64) -> Result<Drawing> {
    let found = Drawing::find_or_404(db, id).await?;
    match owner_id(db, user).await? {
        Some(owner) if owner == found.user_id => Ok(found),
        _ => Err(Error::NotFound),
    }
}

async fn image(
    State(state): State<AppState>,
    user: AuthUser,
    Path(id): Path<i64>,
) -> Result<Response> {
    let found = visible_drawing(&state.db, &user, id).await?;
    let bytes = state
        .storage
        .get(&found.image_path)
        .await?
        .ok_or(Error::NotFound)?;
    let content_type = match found.image_path.rsplit('.').next() {
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
