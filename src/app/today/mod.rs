//! `/today`: what to do today, ticked off right there.
//!
//! The checklist is a live component (`TodayChecklist`). The student ticks tasks; the parent
//! sees the same page read-only (the component refuses the parent's actions).

pub mod models;
pub mod summary;

use crate::app::content::models::{PlanDay, PlanTask, Subject, Topic};
use models::{StudySession, TaskCheck};
use renox::chrono::NaiveDate;
use renox::live_component::{LiveContext, Mounted};
use renox::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

const PLAN_START: (i32, u32, u32) = (2026, 10, 12);
const PLAN_END: (i32, u32, u32) = (2026, 11, 15);
/// Note of the study session that records a finished plan day.
const DONE_NOTE: &str = "Completed the plan for the day";

fn ymd((y, m, d): (i32, u32, u32)) -> NaiveDate {
    NaiveDate::from_ymd_opt(y, m, d).expect("valid date")
}

pub struct Today;

impl Module for Today {
    fn name(&self) -> &'static str {
        "today"
    }

    fn register(&self, app: &mut Registry) {
        app.model::<TaskCheck>();
        app.model::<StudySession>();
        app.view_data::<TodayPage>();
        app.live_component::<TodayChecklist>();
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/today", index)
            .name("today.index")
            .require_auth()
    }
}

// ---------------------------------------------------------------------------------------------
// Data

/// The student whose checklist is shown: the logged-in student, or (for the parent) the
/// household's student.
async fn student_id(db: &Db, user: &AuthUser) -> Result<Option<i64>> {
    if user.has_role("student") {
        return Ok(Some(user.id));
    }
    Ok(renox::db::sql(
        "SELECT ru.user_id FROM role_user ru JOIN roles r ON r.id = ru.role_id \
         WHERE r.name = 'student' ORDER BY ru.user_id LIMIT 1",
    )
    .scalar_optional(db)
    .await?)
}

#[derive(Serialize)]
struct TaskView {
    id: i64,
    label: String,
    checked: bool,
}

#[derive(Serialize)]
struct BlockView {
    label: String,
    minutes: i64,
    tasks: Vec<TaskView>,
}

struct Checklist {
    day: PlanDay,
    blocks: Vec<BlockView>,
    done: i64,
    total: i64,
}

/// The day's blocks (consecutive tasks with the same block label) and which tasks are ticked.
async fn load_checklist(db: &Db, user_id: i64, date: NaiveDate) -> Result<Option<Checklist>> {
    let Some(day) = PlanDay::query()
        .where_(PlanDay::DATE.eq(date))
        .first(db)
        .await?
    else {
        return Ok(None);
    };
    let tasks = PlanTask::query()
        .where_(PlanTask::PLAN_DAY_ID.eq(day.id))
        .order_by(PlanTask::POSITION)
        .get(db)
        .await?;
    let ticked: Vec<i64> = renox::db::sql(
        "SELECT plan_task_id FROM task_checks WHERE user_id = ? \
         AND plan_task_id IN (SELECT id FROM plan_tasks WHERE plan_day_id = ?)",
    )
    .bind(user_id)
    .bind(day.id)
    .scalars(db)
    .await?;
    let mut blocks: Vec<BlockView> = Vec::new();
    let mut done = 0;
    for t in &tasks {
        let checked = ticked.contains(&t.id);
        done += i64::from(checked);
        if blocks.last().is_none_or(|b| b.label != t.block_label) {
            blocks.push(BlockView {
                label: t.block_label.clone(),
                minutes: t.block_minutes,
                tasks: Vec::new(),
            });
        }
        if let Some(b) = blocks.last_mut() {
            b.tasks.push(TaskView {
                id: t.id,
                label: t.label.clone(),
                checked,
            });
        }
    }
    Ok(Some(Checklist {
        day,
        blocks,
        done,
        total: tasks.len() as i64,
    }))
}

// ---------------------------------------------------------------------------------------------
// The live checklist

/// State carried by the browser (signed). `readonly` and `user_id` are set when the page is
/// built and cannot be changed by the browser; the actions check them again anyway.
#[derive(Serialize, Deserialize, Default)]
pub struct TodayChecklist {
    /// The student whose ticks these are.
    user_id: i64,
    date: String,
    readonly: bool,
}

#[renox::live_component(view = "today/_checklist.html", name = "today-checklist")]
impl TodayChecklist {
    async fn data(&self, ctx: &LiveContext) -> Result<renox::serde_json::Value> {
        let date = self.parsed_date()?;
        let list = load_checklist(&ctx.state().db, self.user_id, date).await?;
        Ok(match list {
            Some(l) => {
                let percent = if l.total == 0 {
                    0
                } else {
                    l.done * 100 / l.total
                };
                json!({
                    "blocks": l.blocks, "done": l.done, "total": l.total, "percent": percent,
                    "complete": l.total > 0 && l.done == l.total,
                })
            }
            None => json!({ "blocks": [], "done": 0, "total": 0, "percent": 0, "complete": false }),
        })
    }

    /// Ticks the task, or unticks it when it is ticked.
    #[live(action)]
    async fn toggle(&mut self, ctx: &mut LiveContext, task_id: i64) -> Result {
        // Only the student themselves may change the checklist; the parent is read-only.
        let user = ctx.user()?;
        if self.readonly || !user.has_role("student") || user.id != self.user_id {
            return Err(Error::Forbidden);
        }
        let db = ctx.state().db.clone();
        let date = self.parsed_date()?;
        let day = PlanDay::query()
            .where_(PlanDay::DATE.eq(date))
            .first(&db)
            .await?
            .ok_or(Error::NotFound)?;
        let task = PlanTask::find(&db, task_id).await?.ok_or(Error::NotFound)?;
        if task.plan_day_id != day.id {
            return Err(Error::NotFound);
        }
        let ticked = TaskCheck::query()
            .where_(TaskCheck::USER_ID.eq(self.user_id))
            .where_(TaskCheck::PLAN_TASK_ID.eq(task_id))
            .first(&db)
            .await?;
        match ticked {
            Some(check) => {
                renox::db::sql("DELETE FROM task_checks WHERE id = ?")
                    .bind(check.id)
                    .execute(&db)
                    .await?;
            }
            None => {
                TaskCheck::create(
                    &db,
                    TaskCheck {
                        user_id: self.user_id,
                        plan_task_id: task_id,
                        checked_at: renox::db::now(),
                        ..Default::default()
                    },
                )
                .await?;
            }
        }
        self.record_completion(ctx, &db, &day).await
    }
}

impl TodayChecklist {
    /// The checklist of `date` for the student `user_id`.
    pub fn new(user_id: i64, date: NaiveDate, readonly: bool) -> Self {
        Self {
            user_id,
            date: date.to_string(),
            readonly,
        }
    }

    fn parsed_date(&self) -> Result<NaiveDate> {
        NaiveDate::parse_from_str(&self.date, "%Y-%m-%d")
            .map_err(|_| Error::BadRequest("Invalid date.".into()))
    }

    /// Records the day as completed (a study session + a toast) when every task is ticked, and
    /// takes the record back when a task is unticked again.
    async fn record_completion(&self, ctx: &mut LiveContext, db: &Db, day: &PlanDay) -> Result {
        let Some(list) = load_checklist(db, self.user_id, day.date).await? else {
            return Ok(());
        };
        let recorded: i64 = renox::db::sql(
            "SELECT COUNT(*) FROM study_sessions WHERE user_id = ? AND date = ? AND note = ?",
        )
        .bind(self.user_id)
        .bind(day.date.to_string())
        .bind(DONE_NOTE)
        .scalar(db)
        .await?;
        if list.total > 0 && list.done == list.total {
            if recorded == 0 {
                StudySession::create(
                    db,
                    StudySession {
                        user_id: self.user_id,
                        date: day.date,
                        minutes: day.minutes,
                        subject: day.subject.clone(),
                        note: DONE_NOTE.to_owned(),
                        ..Default::default()
                    },
                )
                .await?;
            }
            ctx.toast(Toast::success("Today is done! 🎉"));
        } else if recorded > 0 {
            renox::db::sql(
                "DELETE FROM study_sessions WHERE user_id = ? AND date = ? AND note = ?",
            )
            .bind(self.user_id)
            .bind(day.date.to_string())
            .bind(DONE_NOTE)
            .execute(db)
            .await?;
        }
        Ok(())
    }
}

// ---------------------------------------------------------------------------------------------
// The page

#[derive(Deserialize)]
struct DateQuery {
    date: Option<String>,
}

#[derive(Serialize)]
struct DayHead {
    title: String,
    phase: &'static str,
    minutes: i64,
    subject_name: String,
    color: String,
    emoji: String,
    /// `false` for diagnostic / mixed / prep / exam days: grey chip with an icon.
    is_subject: bool,
    icon: &'static str,
    issue_url: Option<String>,
}

#[derive(Serialize)]
struct NewMaterial {
    slug: String,
    name: String,
    color: String,
}

#[derive(Serialize)]
struct TimerBlock {
    /// "Block 2" (the part of the label before the colon), safe inside a JS string.
    label: String,
    minutes: i64,
    /// "50:00".
    clock: String,
}

#[derive(Serialize)]
struct EmptyState {
    title: String,
    message: String,
    action_label: String,
    action_date: String,
}

#[derive(Serialize, ViewData)]
#[view(template = "today/index.html")]
struct TodayPage {
    title: &'static str,
    long_date: String,
    iso_date: String,
    prev_date: Option<String>,
    next_date: Option<String>,
    is_today: bool,
    readonly: bool,
    day: Option<DayHead>,
    empty: Option<EmptyState>,
    checklist: Option<Mounted>,
    new_material: Vec<NewMaterial>,
    timer_blocks: Vec<TimerBlock>,
    flashcards_due: i64,
    errors_due: i64,
}

fn phase_label(phase: &str) -> &'static str {
    match phase {
        "intensive" => "Intensive 4-hour holiday",
        "daily" => "30-minute routine",
        "weekend" => "Weekend session",
        "readiness" => "Readiness check",
        "exam" => "Exam day",
        _ => "Study day",
    }
}

fn non_subject_icon(slug: &str) -> &'static str {
    match slug {
        "diagnostic" => "🩺",
        "mixed" => "🔀",
        "review" => "🔁",
        "prep" => "📋",
        "exam" => "🏁",
        _ => "📖",
    }
}

async fn index(
    ctx: LiveContext,
    user: AuthUser,
    State(db): State<Db>,
    Query(q): Query<DateQuery>,
) -> Result<View> {
    let today = crate::clock::today();
    let date = q
        .date
        .as_deref()
        .and_then(|d| NaiveDate::parse_from_str(d, "%Y-%m-%d").ok())
        .unwrap_or(today);
    let (start, end) = (ymd(PLAN_START), ymd(PLAN_END));
    let readonly = !user.has_role("student");
    let student = student_id(&db, &user).await?;

    let mut page = TodayPage {
        title: "Today",
        long_date: date.format("%A, %-d %B %Y").to_string(),
        iso_date: date.to_string(),
        prev_date: (date > start && date <= end)
            .then(|| (date.pred_opt().unwrap_or(date)).to_string()),
        next_date: (date >= start && date < end)
            .then(|| (date.succ_opt().unwrap_or(date)).to_string()),
        is_today: date == today,
        readonly,
        day: None,
        empty: None,
        checklist: None,
        new_material: Vec::new(),
        timer_blocks: Vec::new(),
        flashcards_due: 0,
        errors_due: 0,
    };

    if date < start || date > end {
        page.empty = Some(if date < start {
            EmptyState {
                title: "The plan starts on 12 October".into(),
                message: "Nothing to do yet. Enjoy the time before the study plan begins.".into(),
                action_label: "See the first day".into(),
                action_date: start.to_string(),
            }
        } else {
            EmptyState {
                title: "HUSO Round 1 is over — good luck!".into(),
                message: "The study plan ended on 15 November.".into(),
                action_label: "See the last day".into(),
                action_date: end.to_string(),
            }
        });
        return Ok(View::typed(page));
    }

    let Some(student) = student else {
        page.empty = Some(EmptyState {
            title: "No student account yet".into(),
            message: "Run the seeder to create the household accounts.".into(),
            action_label: String::new(),
            action_date: String::new(),
        });
        return Ok(View::typed(page));
    };
    page.flashcards_due = summary::flashcards_due(&db, student).await?;
    page.errors_due = summary::errors_due(&db, student).await?;

    let Some(list) = load_checklist(&db, student, date).await? else {
        page.empty = Some(EmptyState {
            title: "No plan for this day".into(),
            message: "Nothing is planned on this date.".into(),
            action_label: String::new(),
            action_date: String::new(),
        });
        return Ok(View::typed(page));
    };

    let subjects: Vec<Subject> = Subject::query()
        .order_by(Subject::POSITION)
        .get(&db)
        .await?;
    let by_id: HashMap<i64, &Subject> = subjects.iter().map(|s| (s.id, s)).collect();
    let subject = subjects.iter().find(|s| s.slug == list.day.subject);
    page.day = Some(DayHead {
        title: list.day.title.clone(),
        phase: phase_label(&list.day.phase),
        minutes: list.day.minutes,
        subject_name: match subject {
            Some(s) => s.name.clone(),
            None => {
                let mut name = list.day.subject.clone();
                if let Some(c) = name.get_mut(0..1) {
                    c.make_ascii_uppercase();
                }
                name
            }
        },
        color: subject.map_or_else(|| "#6b7280".to_owned(), |s| s.color.clone()),
        emoji: subject.map(|s| s.emoji.clone()).unwrap_or_default(),
        is_subject: subject.is_some(),
        icon: non_subject_icon(&list.day.subject),
        issue_url: list
            .day
            .issue
            .map(|n| format!("https://github.com/arif-rachim/huso-grade-9/issues/{n}")),
    });

    let slugs = list.day.new_subtopics.0.clone();
    if !slugs.is_empty() {
        let mut topics = Topic::query()
            .where_in("slug", slugs.clone())
            .get(&db)
            .await?;
        topics.sort_by_key(|t| slugs.iter().position(|s| *s == t.slug));
        page.new_material = topics
            .into_iter()
            .map(|t| NewMaterial {
                color: by_id
                    .get(&t.subject_id)
                    .map_or_else(|| "#6b7280".to_owned(), |s| s.color.clone()),
                slug: t.slug,
                name: t.name,
            })
            .collect();
    }
    page.timer_blocks = list
        .blocks
        .iter()
        .map(|b| TimerBlock {
            label: b
                .label
                .split(':')
                .next()
                .unwrap_or_default()
                .chars()
                .filter(|c| c.is_alphanumeric() || *c == ' ')
                .collect(),
            minutes: b.minutes,
            clock: format!("{:02}:00", b.minutes),
        })
        .collect();

    let checklist = TodayChecklist::new(student, date, readonly);
    page.checklist = Some(ctx.mount(checklist).await?);
    Ok(View::typed(page))
}
