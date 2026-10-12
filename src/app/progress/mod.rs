//! `/progress`: before-vs-after charts and the log of practice done outside the app (paper tests,
//! AMC, Physics Bowl ...). `/progress/log` is where the student writes it down.
//!
//! The student writes; the parent sees the same page read-only (the write routes need the
//! `student` role and the templates hide their buttons).

pub mod models;
pub mod stats;

use crate::app::content::models::{Subject, Topic};
use crate::app::practice::scoring::{Tally, format_percent, format_quarters};
use models::{DIAGNOSTIC_SOURCE, ExternalLog};
use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::{Deserialize, Serialize};
use stats::{Bars, BeforeAfter, SeriesOut, Simulation, SourceTotal};
use std::collections::{BTreeSet, HashMap};

const STUDENT: &str = "student";
/// Dates a log may have.
const FIRST_DAY: (i32, u32, u32) = (2026, 10, 1);
const LAST_DAY: (i32, u32, u32) = (2026, 11, 30);
/// The first day of the study plan: where the minutes chart starts.
const PLAN_START: (i32, u32, u32) = (2026, 10, 12);

fn ymd((y, m, d): (i32, u32, u32)) -> NaiveDate {
    NaiveDate::from_ymd_opt(y, m, d).expect("valid date")
}

pub struct Progress;

impl Module for Progress {
    fn name(&self) -> &'static str {
        "progress"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<ExternalLog>();
        app.view_data::<ProgressPage>();
    }

    fn routes(&self) -> Routes {
        // Student and parent: the charts and the history (the parent only reads).
        let shared = Routes::new()
            .get("/progress", index)
            .name("progress.index")
            .require_auth();
        // Only the student writes.
        let student = Routes::new()
            .get("/progress/log", log_page)
            .name("progress.log")
            .post("/progress/log", store)
            .name("progress.log.store")
            .post("/progress/log/diagnostic", store_diagnostic)
            .name("progress.log.diagnostic")
            .get("/progress/log/{id}/edit", edit)
            .name("progress.log.edit")
            .put("/progress/log/{id}", update)
            .name("progress.log.update")
            .delete("/progress/log/{id}", destroy)
            .name("progress.log.destroy")
            .require_role(STUDENT);
        shared.merge(student)
    }
}

// ---- sources.json ---------------------------------------------------------------------------

struct Sources {
    /// `(value, label)` of the select: past papers by slug, practice sources by title.
    options: Vec<(String, String)>,
    /// The diagnostic pack: `(subject slug, number of questions if known)`.
    diagnostic: Vec<(String, Option<i64>)>,
}

fn sources() -> Sources {
    const SOURCES: &str = include_str!("../../../content/sources.json");
    let json: renox::serde_json::Value = renox::serde_json::from_str(SOURCES).unwrap_or_default();
    let mut options = Vec::new();
    let mut diagnostic = Vec::new();
    for p in json["past_papers"].as_array().into_iter().flatten() {
        // Only packs with exam sections are something to score.
        let Some(sections) = p["sections"].as_array() else {
            continue;
        };
        let (Some(slug), Some(title)) = (p["slug"].as_str(), p["title"].as_str()) else {
            continue;
        };
        options.push((slug.to_owned(), title.to_owned()));
        if slug == DIAGNOSTIC_SOURCE {
            for s in sections {
                if let Some(subject) = s["subject"].as_str() {
                    diagnostic.push((subject.to_owned(), s["questions"].as_i64()));
                }
            }
        }
    }
    let mut seen = BTreeSet::new();
    for list in json["practice"]
        .as_object()
        .into_iter()
        .flat_map(|o| o.values())
    {
        for item in list.as_array().into_iter().flatten() {
            if let Some(title) = item["title"].as_str()
                && seen.insert(title.to_owned())
            {
                options.push((title.to_owned(), title.to_owned()));
            }
        }
    }
    Sources {
        options,
        diagnostic,
    }
}

impl Sources {
    /// What to show for a stored source: the paper's title, or the text itself.
    fn title(&self, source: &str) -> String {
        self.options
            .iter()
            .find(|(v, _)| v == source)
            .map_or_else(|| source.to_owned(), |(_, l)| l.clone())
    }
}

// ---- /progress ------------------------------------------------------------------------------

#[derive(Serialize)]
struct LogRow {
    id: i64,
    date: String,
    source: String,
    subject: String,
    color: String,
    topic: String,
    correct: i64,
    wrong: i64,
    blank: i64,
    percent: String,
    score: String,
    minutes: i64,
    note: String,
}

#[derive(Serialize)]
struct Figures {
    questions: i64,
    accuracy: String,
    cards: i64,
    streak: i64,
    week_minutes: i64,
}

#[derive(Serialize, ViewData)]
#[view(template = "progress/index.html")]
struct ProgressPage {
    title: &'static str,
    is_parent: bool,
    figures: Figures,
    /// Colours of the subjects, in series order (for the charts).
    colors: Vec<String>,
    before_after: Vec<BeforeAfter>,
    /// Chart data: labels are the subjects, series "Diagnostic" and "Latest".
    ba_labels: Vec<String>,
    ba_series: Vec<SeriesOut>,
    has_before_after: bool,
    trend: Bars,
    accuracy: Bars,
    minutes_day: Bars,
    minutes_week: Bars,
    simulation: Option<Simulation>,
    sim_missing: Vec<String>,
    logs: Vec<LogRow>,
    totals: Vec<SourceTotal>,
}

async fn index(State(state): State<AppState>, user: AuthUser) -> Result<View> {
    let db = &state.db;
    let today = crate::clock::today();
    let is_parent = !user.has_role(STUDENT);
    let student = crate::app::today::student_id(db, &user).await?;
    let data = match student {
        Some(id) => stats::load(db, id).await?,
        None => stats::load(db, 0).await?,
    };
    let src = sources();
    let subjects = &data.subjects;

    let before_after = stats::before_after(subjects, &data.entries);
    let has_before_after = before_after
        .iter()
        .any(|b| b.before.is_some() || b.after.is_some());
    let ba_labels = before_after.iter().map(|b| b.name.clone()).collect();
    let ba_series = vec![
        SeriesOut {
            name: "Diagnostic".into(),
            values: before_after.iter().map(|b| b.before).collect(),
        },
        SeriesOut {
            name: "Latest".into(),
            values: before_after.iter().map(|b| b.after).collect(),
        },
    ];

    let by_subject = stats::totals_by_subject(&data.entries);
    let accuracy = Bars {
        labels: subjects.iter().map(|s| s.name.clone()).collect(),
        series: vec![SeriesOut {
            name: "Percent correct".into(),
            values: subjects
                .iter()
                .map(|s| {
                    by_subject
                        .get(&s.slug)
                        .filter(|t| t.total() > 0)
                        .map(|t| t.percent_bp() as f64 / 100.0)
                })
                .collect(),
        }],
    };

    let overall = by_subject.values().fold(Tally::default(), |a, b| Tally {
        correct: a.correct + b.correct,
        wrong: a.wrong + b.wrong,
        blank: a.blank + b.blank,
    });
    let study_days: BTreeSet<NaiveDate> = data
        .minutes
        .iter()
        .filter(|(_, m)| **m > 0)
        .map(|(d, _)| *d)
        .collect();
    let this_week = stats::monday(today);
    let figures = Figures {
        questions: overall.total(),
        accuracy: if overall.total() > 0 {
            format!("{}%", format_percent(overall.percent_bp()))
        } else {
            "–".into()
        },
        cards: data.cards_mastered,
        streak: stats::streak(&study_days, today),
        week_minutes: data
            .minutes
            .range(this_week..=today.max(this_week))
            .map(|(_, m)| m)
            .sum(),
    };

    let simulation = stats::simulation(subjects, &data.entries);
    let latest = stats::latest(&data.entries);
    let sim_missing = if simulation.is_none() {
        subjects
            .iter()
            .filter(|s| !latest.contains_key(&s.slug))
            .map(|s| s.name.clone())
            .collect()
    } else {
        Vec::new()
    };

    let topics = topic_names(db).await?;
    let by_slug: HashMap<&str, &Subject> = subjects.iter().map(|s| (s.slug.as_str(), s)).collect();
    let logs = data
        .logs
        .iter()
        .rev()
        .map(|l| {
            let t = l.tally();
            let subject = by_slug.get(l.subject.as_str());
            LogRow {
                id: l.id,
                date: l.date.format("%a %-d %b").to_string(),
                source: src.title(&l.source),
                subject: subject.map_or_else(|| l.subject.clone(), |s| s.name.clone()),
                color: subject.map(|s| s.color.clone()).unwrap_or_default(),
                topic: l
                    .topic_id
                    .and_then(|id| topics.get(&id).cloned())
                    .unwrap_or_default(),
                correct: l.correct,
                wrong: l.wrong,
                blank: l.blank,
                percent: format_percent(t.percent_bp()),
                score: format_quarters(t.raw_q()),
                minutes: l.minutes,
                note: l.note.clone(),
            }
        })
        .collect();

    Ok(View::typed(ProgressPage {
        title: "Progress",
        is_parent,
        figures,
        colors: subjects.iter().map(|s| s.color.clone()).collect(),
        before_after,
        ba_labels,
        ba_series,
        has_before_after,
        trend: stats::weekly_trend(subjects, &data.entries, today),
        accuracy,
        minutes_day: stats::minutes_per_day(&data.minutes, &data.plan, ymd(PLAN_START), today),
        minutes_week: stats::minutes_per_week(&data.minutes, today),
        simulation,
        sim_missing,
        logs,
        totals: stats::source_totals(&data.logs, |s| src.title(s)),
    }))
}

/// Subtopic id -> name.
async fn topic_names(db: &Db) -> Result<HashMap<i64, String>> {
    let rows: Vec<(i64, String)> =
        renox::db::sql("SELECT id, name FROM topics WHERE parent_id IS NOT NULL")
            .fetch_as(db)
            .await?;
    Ok(rows.into_iter().collect())
}

// ---- /progress/log ---------------------------------------------------------------------------

async fn subject_options(db: &Db) -> Result<Vec<Subject>> {
    Subject::query().order_by(Subject::POSITION).get(db).await
}

async fn subtopic_options(db: &Db, subjects: &[Subject]) -> Result<Vec<(String, String)>> {
    let subtopics = Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::POSITION)
        .get(db)
        .await?;
    let mut options = Vec::new();
    for s in subjects {
        for t in subtopics.iter().filter(|t| t.subject_id == s.id) {
            options.push((t.id.to_string(), format!("{} · {}", s.name, t.name)));
        }
    }
    Ok(options)
}

#[derive(Serialize)]
struct DiagRowView {
    index: usize,
    slug: String,
    name: String,
    color: String,
    questions: Option<i64>,
}

fn diagnostic_rows(subjects: &[Subject], src: &Sources) -> Vec<DiagRowView> {
    subjects
        .iter()
        .enumerate()
        .map(|(index, s)| DiagRowView {
            index,
            slug: s.slug.clone(),
            name: s.name.clone(),
            color: s.color.clone(),
            questions: src
                .diagnostic
                .iter()
                .find(|(slug, _)| *slug == s.slug)
                .and_then(|(_, q)| *q),
        })
        .collect()
}

async fn log_page(State(state): State<AppState>) -> Result<View> {
    let db = &state.db;
    let src = sources();
    let subjects = subject_options(db).await?;
    Ok(view(
        "progress/log.html",
        context! {
            title => "Log practice",
            today => crate::clock::today().to_string(),
            first_day => ymd(FIRST_DAY).to_string(),
            last_day => ymd(LAST_DAY).to_string(),
            sources => src.options.clone(),
            subjects => subjects.iter().map(|s| (s.slug.clone(), s.name.clone())).collect::<Vec<_>>(),
            subtopics => subtopic_options(db, &subjects).await?,
            diagnostic_rows => diagnostic_rows(&subjects, &src),
            diagnostic_title => src.title(DIAGNOSTIC_SOURCE),
        },
    ))
}

fn clean(value: &Option<String>) -> Option<String> {
    value
        .as_deref()
        .map(str::trim)
        .filter(|v| !v.is_empty())
        .map(str::to_owned)
}

/// A count must not be negative.
fn count_rule(v: &mut Validator, field: &str, value: Option<i64>) {
    if value.is_some_and(|n| n < 0) {
        v.error(field, "Use 0 or more.");
    }
}

fn date_rule(v: &mut Validator, field: &str, date: Option<NaiveDate>) {
    match date {
        None => v.error(field, "Pick a date."),
        Some(d) if d < ymd(FIRST_DAY) || d > ymd(LAST_DAY) => {
            v.error(field, "Pick a date between 1 Oct and 30 Nov 2026.");
        }
        Some(_) => {}
    }
}

#[derive(Deserialize)]
struct LogForm {
    date: Option<NaiveDate>,
    source: Option<String>,
    source_other: Option<String>,
    subject: Option<String>,
    topic: Option<i64>,
    correct: Option<i64>,
    wrong: Option<i64>,
    blank: Option<i64>,
    minutes: Option<i64>,
    note: Option<String>,
}

impl Validate for LogForm {
    fn rules(&self, v: &mut Validator) {
        date_rule(v, "date", self.date);
        if clean(&self.source).is_none() && clean(&self.source_other).is_none() {
            v.error("source", "Pick a source or write another one.");
        }
        v.field("source_other", &self.source_other).max(120);
        v.field("subject", &self.subject).required();
        v.field("note", &self.note).max(1000);
        for (name, n) in [
            ("correct", self.correct),
            ("wrong", self.wrong),
            ("blank", self.blank),
            ("minutes", self.minutes),
        ] {
            count_rule(v, name, n);
        }
        let questions =
            self.correct.unwrap_or(0) + self.wrong.unwrap_or(0) + self.blank.unwrap_or(0);
        if questions <= 0
            && [self.correct, self.wrong, self.blank]
                .iter()
                .all(|n| n.is_none_or(|n| n >= 0))
        {
            v.error("correct", "Correct + wrong + blank must be more than 0.");
        }
    }
}

impl LogForm {
    fn tally(&self) -> Tally {
        Tally {
            correct: self.correct.unwrap_or(0),
            wrong: self.wrong.unwrap_or(0),
            blank: self.blank.unwrap_or(0),
        }
    }

    /// Fills a log with the form's values (the subject must be checked first).
    fn fill(&self, log: &mut ExternalLog) {
        let t = self.tally();
        log.date = self.date.unwrap_or_default();
        log.source = clean(&self.source_other)
            .or_else(|| clean(&self.source))
            .unwrap_or_default();
        log.subject = self.subject.clone().unwrap_or_default();
        log.topic_id = self.topic;
        log.correct = t.correct;
        log.wrong = t.wrong;
        log.blank = t.blank;
        log.minutes = self.minutes.unwrap_or(0);
        log.note = clean(&self.note).unwrap_or_default();
    }
}

/// The subject slug must be one of the app's subjects, and a subtopic must belong to it.
async fn check_subject_and_topic(db: &Db, subject: &str, topic: Option<i64>) -> Result<()> {
    let subjects = subject_options(db).await?;
    let Some(s) = subjects.iter().find(|s| s.slug == subject) else {
        return Err(abort(StatusCode::UNPROCESSABLE_ENTITY, "Pick a subject."));
    };
    if let Some(id) = topic {
        let topic = Topic::find_or_404(db, id).await?;
        if topic.parent_id.is_none() || topic.subject_id != s.id {
            return Err(abort(
                StatusCode::UNPROCESSABLE_ENTITY,
                "Pick a subtopic of that subject.",
            ));
        }
    }
    Ok(())
}

/// The toast after saving: it offers to add the wrong questions to the Error Log.
fn saved_toast(message: &str) -> Result<Toast> {
    // EXTENSION POINT: the manual form of the Error Log cannot be pre-filled with the source
    // yet; when it can, add the log's source to this link.
    Ok(Toast::success(message).link("Add the wrong questions to the Error Log", "/errors/new"))
}

async fn store(
    State(state): State<AppState>,
    user: AuthUser,
    Valid(form): Valid<LogForm>,
) -> Result<impl IntoResponse> {
    let db = &state.db;
    let subject = form.subject.clone().unwrap_or_default();
    check_subject_and_topic(db, &subject, form.topic).await?;
    let mut log = ExternalLog {
        user_id: user.id,
        ..Default::default()
    };
    form.fill(&mut log);
    ExternalLog::create(db, log).await?;
    Ok((
        saved_toast("Practice saved.")?,
        Redirect::route("progress.index", &[])?,
    ))
}

#[derive(Deserialize, Default)]
struct DiagRow {
    #[serde(default)]
    subject: String,
    correct: Option<i64>,
    wrong: Option<i64>,
    blank: Option<i64>,
    minutes: Option<i64>,
}

impl DiagRow {
    fn tally(&self) -> Tally {
        Tally {
            correct: self.correct.unwrap_or(0),
            wrong: self.wrong.unwrap_or(0),
            blank: self.blank.unwrap_or(0),
        }
    }
}

#[derive(Deserialize)]
struct DiagnosticForm {
    date: Option<NaiveDate>,
    #[serde(default)]
    rows: Vec<DiagRow>,
}

impl Validate for DiagnosticForm {
    fn rules(&self, v: &mut Validator) {
        date_rule(v, "date", self.date);
        let mut any = false;
        for (i, r) in self.rows.iter().enumerate() {
            count_rule(v, &format!("rows.{i}.correct"), r.correct);
            count_rule(v, &format!("rows.{i}.wrong"), r.wrong);
            count_rule(v, &format!("rows.{i}.blank"), r.blank);
            count_rule(v, &format!("rows.{i}.minutes"), r.minutes);
            any |= r.tally().total() > 0;
        }
        if !any {
            v.error("date", "Fill in the numbers of at least one subject.");
        }
    }
}

async fn store_diagnostic(
    State(state): State<AppState>,
    user: AuthUser,
    Valid(form): Valid<DiagnosticForm>,
) -> Result<impl IntoResponse> {
    let db = &state.db;
    let subjects = subject_options(db).await?;
    let mut saved = 0;
    for r in form.rows.iter().filter(|r| r.tally().total() > 0) {
        if !subjects.iter().any(|s| s.slug == r.subject) {
            return Err(abort(StatusCode::UNPROCESSABLE_ENTITY, "Unknown subject."));
        }
        let t = r.tally();
        ExternalLog::create(
            db,
            ExternalLog {
                user_id: user.id,
                date: form.date.unwrap_or_default(),
                source: DIAGNOSTIC_SOURCE.into(),
                subject: r.subject.clone(),
                correct: t.correct,
                wrong: t.wrong,
                blank: t.blank,
                minutes: r.minutes.unwrap_or(0),
                ..Default::default()
            },
        )
        .await?;
        saved += 1;
    }
    Ok((
        saved_toast(&format!("Diagnostic saved ({saved} subjects)."))?,
        Redirect::route("progress.index", &[])?,
    ))
}

/// The log of this student, or 404.
fn own(log: ExternalLog, user: &AuthUser) -> Result<ExternalLog> {
    if log.user_id == user.id {
        Ok(log)
    } else {
        Err(Error::NotFound)
    }
}

async fn edit(
    State(state): State<AppState>,
    user: AuthUser,
    Found(log): Found<ExternalLog>,
) -> Result<View> {
    let log = own(log, &user)?;
    let src = sources();
    let subjects = subject_options(&state.db).await?;
    // A source that is not in the list is "another source".
    let known = src.options.iter().any(|(v, _)| *v == log.source);
    Ok(view(
        "progress/edit.html",
        context! {
            title => "Edit practice log",
            log => &log,
            source_known => known,
            first_day => ymd(FIRST_DAY).to_string(),
            last_day => ymd(LAST_DAY).to_string(),
            sources => src.options.clone(),
            subjects => subjects.iter().map(|s| (s.slug.clone(), s.name.clone())).collect::<Vec<_>>(),
            subtopics => subtopic_options(&state.db, &subjects).await?,
        },
    ))
}

async fn update(
    State(state): State<AppState>,
    user: AuthUser,
    Found(log): Found<ExternalLog>,
    Valid(form): Valid<LogForm>,
) -> Result<impl IntoResponse> {
    let mut log = own(log, &user)?;
    let subject = form.subject.clone().unwrap_or_default();
    check_subject_and_topic(&state.db, &subject, form.topic).await?;
    form.fill(&mut log);
    log.save(&state.db).await?;
    Ok((
        Toast::success("Practice log updated."),
        Redirect::route("progress.index", &[])?,
    ))
}

async fn destroy(
    State(state): State<AppState>,
    user: AuthUser,
    Found(log): Found<ExternalLog>,
) -> Result<impl IntoResponse> {
    own(log, &user)?.delete(&state.db).await?;
    Ok((Toast::success("Entry deleted."), HxRefresh))
}
