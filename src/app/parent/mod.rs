//! `/parent`: the Parent Dashboard. One read-only screen with the student's consistency and
//! progress. It only reads: it reuses the numbers of the other modules (plan, progress,
//! syllabus, error log, lessons, flashcards) and has no form, button or route that changes data.
//! A constant number of queries, however much data there is.

use crate::app::accounts::PARENT;
use crate::app::content::models::{PlanDay, Topic};
use crate::app::errors::models::{ErrorEntry, cause_label};
use crate::app::lessons::status::{self as lesson_status, Status as LessonStatus};
use crate::app::plan::{self, Status as DayStatus};
use crate::app::practice::engine::student_user_id;
use crate::app::practice::scoring::format_percent;
use crate::app::progress::stats;
use crate::app::{flashcards, syllabus};
use renox::chrono::{Datelike, Duration, NaiveDate};
use renox::prelude::*;
use serde::Serialize;
use std::collections::{BTreeSet, HashMap};

/// Where the HUSO registration reminder points.
pub const REGISTRATION_ISSUE: &str = "https://github.com/arif-rachim/huso-grade-9/issues/2";
/// The reminder shows up to and including this day.
const REGISTRATION_LAST_DAY: (i32, u32, u32) = (2026, 10, 31);
/// The first and last day of the study plan.
const PLAN_START: (i32, u32, u32) = (2026, 10, 12);
const PLAN_END: (i32, u32, u32) = (2026, 11, 15);
/// Days shown in the mini calendar (two weeks, ending today).
const CALENDAR_DAYS: i64 = 14;
const LIST_LEN: usize = 5;

fn ymd((y, m, d): (i32, u32, u32)) -> NaiveDate {
    NaiveDate::from_ymd_opt(y, m, d).expect("valid date")
}

pub struct Parent;

impl Module for Parent {
    fn name(&self) -> &'static str {
        "parent"
    }

    fn register(&self, app: &mut Registry) {
        app.view_data::<ParentPage>();
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/parent", index)
            .name("parent.index")
            .require_role(PARENT)
    }
}

// ---- pure logic (unit tested below) -----------------------------------------------------------

/// Did the student do nothing on each of the last two days, and nothing yet today? Only inside
/// the study plan (the first two plan days cannot trigger it).
pub fn no_activity_warning(active: &BTreeSet<NaiveDate>, today: NaiveDate) -> bool {
    let (first, last) = (ymd(PLAN_START), ymd(PLAN_END));
    let one = today - Duration::days(1);
    let two = today - Duration::days(2);
    today >= first + Duration::days(2)
        && today <= last
        && ![today, one, two].iter().any(|d| active.contains(d))
}

/// The registration reminder is shown while `today <= 31 Oct`.
pub fn registration_reminder(today: NaiveDate) -> bool {
    today <= ymd(REGISTRATION_LAST_DAY)
}

fn percent(bp: i64) -> String {
    format!("{}%", format_percent(bp))
}

/// Percent with one decimal for a `correct / total` pair, `None` without answers.
fn accuracy(correct: i64, total: i64) -> Option<String> {
    (total > 0).then(|| percent(crate::app::practice::scoring::percent_bp(correct, total)))
}

// ---- data -------------------------------------------------------------------------------------

/// The dates (Jakarta) on which the student did anything: ticked a task, reviewed a card,
/// answered a question, logged study time or a paper test. One query.
async fn active_days(db: &Db, user_id: i64) -> Result<BTreeSet<NaiveDate>> {
    let days: Vec<String> = renox::db::sql(
        "SELECT date(checked_at, '+7 hours') FROM task_checks WHERE user_id = ? \
         UNION SELECT date(reviewed_at, '+7 hours') FROM card_reviews WHERE user_id = ? \
         UNION SELECT date(a.answered_at, '+7 hours') FROM answers a \
               JOIN attempts t ON t.id = a.attempt_id \
               WHERE t.user_id = ? AND a.answered_at IS NOT NULL \
         UNION SELECT date FROM study_sessions WHERE user_id = ? \
         UNION SELECT date FROM external_logs WHERE user_id = ?",
    )
    .bind(user_id)
    .bind(user_id)
    .bind(user_id)
    .bind(user_id)
    .bind(user_id)
    .scalars(db)
    .await?;
    Ok(days.iter().filter_map(|d| d.parse().ok()).collect())
}

/// `(correct, answered)` over the answers given since `since` (a Jakarta date). One query.
async fn answers_since(db: &Db, user_id: i64, since: NaiveDate) -> Result<(i64, i64)> {
    let row: (i64, i64) = renox::db::sql(
        "SELECT COALESCE(SUM(a.is_correct), 0), COUNT(*) FROM answers a \
         JOIN attempts t ON t.id = a.attempt_id \
         WHERE t.user_id = ? AND a.choice IS NOT NULL \
           AND date(a.answered_at, '+7 hours') >= ?",
    )
    .bind(user_id)
    .bind(since.to_string())
    .fetch_one_as(db)
    .await?;
    Ok(row)
}

// ---- the page ---------------------------------------------------------------------------------

#[derive(Serialize)]
struct Today {
    title: String,
    phase: String,
    done: i64,
    total: i64,
    percent: i64,
}

#[derive(Serialize)]
struct CalendarDay {
    date: String,
    day: u32,
    weekday: &'static str,
    status: &'static str,
    label: String,
    is_today: bool,
}

#[derive(Serialize)]
struct SubjectRow {
    name: String,
    emoji: String,
    color: String,
    percent: Option<String>,
    width: i64,
    weakest: bool,
}

#[derive(Serialize)]
struct Subtopic {
    slug: String,
    name: String,
    subject_name: String,
    color: String,
    mastery: i32,
}

#[derive(Serialize)]
struct ErrorRow {
    subject_name: String,
    color: String,
    topic: String,
    cause: &'static str,
    has_cause: bool,
    note: String,
    on: String,
}

#[derive(Serialize)]
struct LessonCounts {
    ready: usize,
    in_progress: usize,
    not_yet: usize,
}

#[derive(Serialize, ViewData)]
#[view(template = "parent/index.html")]
struct ParentPage {
    title: &'static str,
    has_student: bool,
    student_name: String,
    streak: i64,
    days_done: i64,
    days_elapsed: i64,
    minutes_week: i64,
    accuracy_week: Option<String>,
    cards_due: i64,
    today: Option<Today>,
    calendar: Vec<CalendarDay>,
    subjects: Vec<SubjectRow>,
    weakest: Option<String>,
    red_subtopics: Vec<Subtopic>,
    mistakes: Vec<ErrorRow>,
    lessons: LessonCounts,
    warn_inactive: bool,
    warn_registration: bool,
    registration_url: &'static str,
}

const WEEKDAYS: [&str; 7] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

async fn index(State(db): State<Db>) -> Result<View> {
    let today = crate::clock::today();
    let Some(student) = student_user_id(&db).await? else {
        return Ok(View::typed(ParentPage::empty()));
    };
    let student_name: String = renox::db::sql("SELECT name FROM users WHERE id = ?")
        .bind(student)
        .scalar(&db)
        .await?;

    // Plan: days completed, today's checklist and the calendar (2 queries).
    let plan_days = PlanDay::query().order_by(PlanDay::DATE).get(&db).await?;
    let counts = plan::day_counts(&db, student).await?;
    let mut flags: HashMap<NaiveDate, (DayStatus, i64, i64)> = HashMap::new();
    let (mut days_done, mut days_elapsed) = (0, 0);
    let mut today_row = None;
    for d in &plan_days {
        let (total, done) = counts.get(&d.id).copied().unwrap_or((0, 0));
        let status = plan::status_of(d.date, today, done, total);
        days_elapsed += i64::from(d.date <= today);
        days_done += i64::from(status == DayStatus::Done);
        flags.insert(d.date, (status, done, total));
        if d.date == today {
            today_row = Some(Today {
                title: d.title.clone(),
                phase: d.phase.clone(),
                done,
                total,
                percent: plan::percent_of(done, total),
            });
        }
    }
    // The last two weeks, but not before the plan starts.
    let first_day = (today - Duration::days(CALENDAR_DAYS - 1)).max(ymd(PLAN_START));
    let calendar = (0..=(today - first_day).num_days().max(0))
        .map(|n| {
            let date = first_day + Duration::days(n);
            let weekday = WEEKDAYS[date.weekday().num_days_from_monday() as usize];
            let (status, label) = match flags.get(&date) {
                Some((s, done, total)) => (
                    match s {
                        DayStatus::Done => "done",
                        DayStatus::Partial => "partial",
                        DayStatus::Missed => "missed",
                        DayStatus::Pending => "pending",
                        DayStatus::Future => "future",
                    },
                    match s {
                        DayStatus::Done => "Done".to_owned(),
                        DayStatus::Partial | DayStatus::Pending => format!("{done}/{total}"),
                        DayStatus::Missed => "Missed".to_owned(),
                        DayStatus::Future => String::new(),
                    },
                ),
                None => ("future", "No plan".to_owned()),
            };
            CalendarDay {
                date: date.to_string(),
                day: date.day(),
                weekday,
                status,
                label,
                is_today: date == today,
            }
        })
        .collect();

    // Study minutes, latest score per subject (progress module).
    let stats = stats::load(&db, student).await?;
    let week_start = today - Duration::days(6);
    let minutes_week: i64 = stats
        .minutes
        .range(week_start..=today)
        .map(|(_, m)| *m)
        .sum();
    let latest = stats::latest(&stats.entries);
    let mut weakest: Option<(i64, String)> = None;
    let mut subjects = Vec::new();
    for s in &stats.subjects {
        let bp = latest
            .get(&s.slug)
            .filter(|t| t.total() > 0)
            .map(|t| t.percent_bp());
        if let Some(bp) = bp
            && weakest.as_ref().is_none_or(|(w, _)| bp < *w)
        {
            weakest = Some((bp, s.name.clone()));
        }
        subjects.push((s, bp));
    }
    let weakest_name = weakest.map(|(_, n)| n);
    let subjects: Vec<SubjectRow> = subjects
        .into_iter()
        .map(|(s, bp)| SubjectRow {
            name: s.name.clone(),
            emoji: s.emoji.clone(),
            color: s.color.clone(),
            percent: bp.map(percent),
            width: bp.map_or(0, |b| b / 100),
            weakest: weakest_name.as_deref() == Some(s.name.as_str()),
        })
        .collect();

    // Activity, accuracy, due cards.
    let active = active_days(&db, student).await?;
    let (correct, answered) = answers_since(&db, student, week_start).await?;
    let cards_due = flashcards::due_count(&db, student, today).await?;

    // Syllabus: the reddest started subtopics.
    let mastery = syllabus::mastery_by_subtopic(&db, student).await?;
    let total_subtopics = mastery.len();
    let mut reddest: Vec<(String, i32)> = mastery
        .into_iter()
        .filter_map(|(slug, v)| v.map(|v| (slug, v)))
        .collect();
    reddest.sort_by(|a, b| a.1.cmp(&b.1).then_with(|| a.0.cmp(&b.0)));
    reddest.truncate(LIST_LEN);
    let slugs: Vec<String> = reddest.iter().map(|(s, _)| s.clone()).collect();
    let topics: Vec<Topic> = if slugs.is_empty() {
        Vec::new()
    } else {
        Topic::query()
            .where_(Topic::SLUG.is_in(slugs))
            .get(&db)
            .await?
    };
    let subject_by_id: HashMap<i64, &crate::app::content::models::Subject> =
        stats.subjects.iter().map(|s| (s.id, s)).collect();
    let by_slug: HashMap<&str, &Topic> = topics.iter().map(|t| (t.slug.as_str(), t)).collect();
    let red_subtopics = reddest
        .iter()
        .filter_map(|(slug, value)| {
            let topic = by_slug.get(slug.as_str())?;
            let subject = subject_by_id.get(&topic.subject_id)?;
            Some(Subtopic {
                slug: slug.clone(),
                name: topic.name.clone(),
                subject_name: subject.name.clone(),
                color: subject.color.clone(),
                mastery: *value,
            })
        })
        .collect();

    // The latest error log entries with their causes.
    let entries = ErrorEntry::query()
        .where_(ErrorEntry::USER_ID.eq(student))
        .order_by_desc(ErrorEntry::CREATED_AT)
        .order_by_desc(ErrorEntry::ID)
        .limit(LIST_LEN as u64)
        .get(&db)
        .await?;
    let error_topics: HashMap<i64, Topic> =
        Topic::find_many(&db, entries.iter().map(|e| e.topic_id))
            .await?
            .into_iter()
            .map(|t| (t.id, t))
            .collect();
    let errors = entries
        .iter()
        .map(|e| {
            let subject = stats.subjects.iter().find(|s| s.slug == e.subject);
            ErrorRow {
                subject_name: subject.map_or_else(|| e.subject.clone(), |s| s.name.clone()),
                color: subject.map_or_else(|| "#6b7280".to_owned(), |s| s.color.clone()),
                topic: error_topics
                    .get(&e.topic_id)
                    .map_or_else(String::new, |t| t.name.clone()),
                cause: e.cause.as_deref().map_or("Not set", cause_label),
                has_cause: e.has_cause(),
                note: e.note.clone().unwrap_or_default(),
                on: e
                    .created_at
                    .map(|c| c.date_naive().to_string())
                    .unwrap_or_default(),
            }
        })
        .collect();

    // READY / in progress / not yet.
    let states = lesson_status::states(&db, student).await?;
    let ready = states
        .values()
        .filter(|s| s.status == LessonStatus::Ready)
        .count();
    let in_progress = states
        .values()
        .filter(|s| s.status == LessonStatus::InProgress)
        .count();
    let lessons = LessonCounts {
        ready,
        in_progress,
        not_yet: total_subtopics.saturating_sub(ready + in_progress),
    };

    Ok(View::typed(ParentPage {
        title: "Parent Dashboard",
        has_student: true,
        student_name,
        streak: stats::streak(&active, today),
        days_done,
        days_elapsed,
        minutes_week,
        accuracy_week: accuracy(correct, answered),
        cards_due,
        today: today_row,
        calendar,
        subjects,
        weakest: weakest_name,
        red_subtopics,
        mistakes: errors,
        lessons,
        warn_inactive: no_activity_warning(&active, today),
        warn_registration: registration_reminder(today),
        registration_url: REGISTRATION_ISSUE,
    }))
}

impl ParentPage {
    /// The page when the household has no student account yet.
    fn empty() -> Self {
        ParentPage {
            title: "Parent Dashboard",
            has_student: false,
            student_name: String::new(),
            streak: 0,
            days_done: 0,
            days_elapsed: 0,
            minutes_week: 0,
            accuracy_week: None,
            cards_due: 0,
            today: None,
            calendar: Vec::new(),
            subjects: Vec::new(),
            weakest: None,
            red_subtopics: Vec::new(),
            mistakes: Vec::new(),
            lessons: LessonCounts {
                ready: 0,
                in_progress: 0,
                not_yet: 0,
            },
            warn_inactive: false,
            warn_registration: registration_reminder(crate::clock::today()),
            registration_url: REGISTRATION_ISSUE,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(m: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, m, day).unwrap()
    }

    #[test]
    fn two_quiet_days_in_a_row_warn() {
        let active: BTreeSet<_> = [d(10, 14)].into();
        assert!(!no_activity_warning(&active, d(10, 15)));
        assert!(!no_activity_warning(&active, d(10, 16)));
        assert!(no_activity_warning(&active, d(10, 17)));
        // Activity today also silences it.
        let today: BTreeSet<_> = [d(10, 17)].into();
        assert!(!no_activity_warning(&today, d(10, 17)));
    }

    #[test]
    fn no_warning_before_the_plan_has_run_two_days() {
        let none = BTreeSet::new();
        assert!(!no_activity_warning(&none, d(10, 12)));
        assert!(!no_activity_warning(&none, d(10, 13)));
        assert!(no_activity_warning(&none, d(10, 14)));
        assert!(!no_activity_warning(&none, d(11, 16)));
    }

    #[test]
    fn the_registration_reminder_ends_after_31_oct() {
        assert!(registration_reminder(d(10, 31)));
        assert!(!registration_reminder(d(11, 1)));
    }
}
