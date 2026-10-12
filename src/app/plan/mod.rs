//! `/plan`: the wall calendar (a 5 x 7 heatmap of the whole study plan) and
//! `/plan/{date}`: one day, using the same page and live checklist as `/today`.
//!
//! The student sees and ticks; the parent sees the same data read-only (the checklist component
//! refuses the parent's actions, and the calendar only has links).

use crate::app::content::models::{PlanDay, Subject};
use crate::app::today;
use renox::chrono::{Datelike, NaiveDate};
use renox::live_component::LiveContext;
use renox::prelude::*;
use serde::Serialize;
use std::collections::HashMap;

pub struct Plan;

impl Module for Plan {
    fn name(&self) -> &'static str {
        "plan"
    }

    fn register(&self, app: &mut Registry) {
        app.view_data::<PlanPage>();
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/plan", index)
            .name("plan.index")
            .get("/plan/{date}", show)
            .name("plan.show")
            .require_auth()
    }
}

// ---------------------------------------------------------------------------------------------
// Pure calendar logic (unit tested below)

/// How a day looks on the calendar.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Status {
    /// Every task ticked.
    Done,
    /// Some tasks ticked.
    Partial,
    /// A past day with nothing ticked.
    Missed,
    /// Today with nothing ticked yet.
    Pending,
    /// A day that has not come yet.
    Future,
}

impl Status {
    fn slug(self) -> &'static str {
        match self {
            Status::Done => "done",
            Status::Partial => "partial",
            Status::Missed => "missed",
            Status::Pending => "pending",
            Status::Future => "future",
        }
    }
}

/// The status of a day with `done` of `total` tasks ticked, seen from `today`.
pub fn status_of(date: NaiveDate, today: NaiveDate, done: i64, total: i64) -> Status {
    if total > 0 && done >= total {
        Status::Done
    } else if done > 0 && date <= today {
        Status::Partial
    } else if date > today {
        Status::Future
    } else if date == today {
        Status::Pending
    } else {
        Status::Missed
    }
}

/// Percentage of tasks ticked (0 when the day has no tasks).
pub fn percent_of(done: i64, total: i64) -> i64 {
    if total == 0 { 0 } else { done * 100 / total }
}

/// Current and record streak of completed days. `days` are the plan's days in date order as
/// `(date, complete)`. The current streak counts consecutive completed days ending today, or
/// ending yesterday when today is not complete (yet).
pub fn streaks(days: &[(NaiveDate, bool)], today: NaiveDate) -> (i64, i64) {
    let mut record = 0;
    let mut run = 0;
    for (date, complete) in days {
        if *date <= today && *complete {
            run += 1;
            record = record.max(run);
        } else {
            run = 0;
        }
    }
    let mut current = 0;
    let mut expected = today;
    // Today may still be in progress: start from yesterday then.
    if !days.iter().any(|(d, c)| *d == today && *c) {
        expected = today.pred_opt().unwrap_or(today);
    }
    for (date, complete) in days.iter().rev() {
        if *date > expected {
            continue;
        }
        if *date == expected && *complete {
            current += 1;
            expected = expected.pred_opt().unwrap_or(expected);
        } else {
            break;
        }
    }
    (current, record)
}

// ---------------------------------------------------------------------------------------------
// Data

/// `(plan_day_id, tasks, ticked tasks)` for every day, for one student.
async fn day_counts(db: &Db, user_id: i64) -> Result<HashMap<i64, (i64, i64)>> {
    let rows: Vec<(i64, i64, i64)> = renox::db::sql(
        "SELECT d.id, COUNT(t.id), COUNT(c.id) FROM plan_days d \
         LEFT JOIN plan_tasks t ON t.plan_day_id = d.id \
         LEFT JOIN task_checks c ON c.plan_task_id = t.id AND c.user_id = ? \
         GROUP BY d.id",
    )
    .bind(user_id)
    .fetch_as(db)
    .await?;
    Ok(rows.into_iter().map(|(id, n, d)| (id, (n, d))).collect())
}

#[derive(Serialize)]
struct Cell {
    date: String,
    day: u32,
    /// "Oct" on the first cell and on the 1st of a month.
    month: Option<&'static str>,
    title: String,
    subject_name: String,
    color: String,
    /// The subject emoji, or an icon for diagnostic / mixed / prep / exam days.
    emoji: String,
    phase: &'static str,
    minutes: i64,
    done: i64,
    total: i64,
    percent: i64,
    /// Strength of the subject colour for a partial day (30-80).
    fill: i64,
    status: &'static str,
    is_today: bool,
    is_exam: bool,
    aria: String,
}

#[derive(Serialize)]
struct Week {
    label: String,
    /// Set when the phase changes at the start of this week.
    divider: Option<&'static str>,
    cells: Vec<Cell>,
}

#[derive(Serialize)]
struct LegendSubject {
    name: String,
    emoji: String,
    color: String,
}

#[derive(Serialize, ViewData)]
#[view(template = "plan/index.html")]
struct PlanPage {
    title: &'static str,
    weeks: Vec<Week>,
    legend: Vec<LegendSubject>,
    streak: i64,
    record: i64,
    days_done: i64,
    days_passed: i64,
    days_total: i64,
    minutes_done: i64,
    minutes_total: i64,
    readonly: bool,
}

const MONTHS: [&str; 12] = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const WEEKDAYS: [&str; 7] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

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

fn icon(slug: &str) -> &'static str {
    match slug {
        "diagnostic" => "🩺",
        "mixed" => "🔀",
        "review" => "🔁",
        "prep" => "📋",
        "exam" => "🏁",
        _ => "📖",
    }
}

fn short_date(d: NaiveDate) -> String {
    format!("{} {}", d.day(), MONTHS[d.month0() as usize])
}

async fn index(user: AuthUser, State(db): State<Db>) -> Result<View> {
    let today = crate::clock::today();
    let readonly = !user.has_role("student");
    let student = today::student_id(&db, &user).await?;
    let counts = match student {
        Some(id) => day_counts(&db, id).await?,
        None => HashMap::new(),
    };
    let plan = PlanDay::query().order_by(PlanDay::DATE).get(&db).await?;
    let subjects: Vec<Subject> = Subject::query()
        .order_by(Subject::POSITION)
        .get(&db)
        .await?;
    let by_slug: HashMap<&str, &Subject> = subjects.iter().map(|s| (s.slug.as_str(), s)).collect();

    let mut cells: Vec<(Cell, &PlanDay)> = Vec::new();
    let mut flags: Vec<(NaiveDate, bool)> = Vec::new();
    let (mut days_done, mut days_passed) = (0, 0);
    let (mut minutes_done, mut minutes_total) = (0, 0);
    for d in &plan {
        let (total, done) = counts.get(&d.id).copied().unwrap_or((0, 0));
        let status = status_of(d.date, today, done, total);
        let percent = percent_of(done, total);
        flags.push((d.date, status == Status::Done));
        days_passed += i64::from(d.date <= today);
        days_done += i64::from(status == Status::Done);
        minutes_total += d.minutes;
        minutes_done += if total == 0 {
            0
        } else {
            d.minutes * done / total
        };
        let subject = by_slug.get(d.subject.as_str());
        let subject_name = subject.map_or_else(
            || {
                let mut n = d.subject.clone();
                if let Some(c) = n.get_mut(0..1) {
                    c.make_ascii_uppercase();
                }
                n
            },
            |s| s.name.clone(),
        );
        let weekday = WEEKDAYS[d.date.weekday().num_days_from_monday() as usize];
        let status_text = match status {
            Status::Done => "done".to_owned(),
            Status::Partial => format!("{percent}% done"),
            Status::Missed => "missed".to_owned(),
            Status::Pending => "not started".to_owned(),
            Status::Future => "upcoming".to_owned(),
        };
        cells.push((
            Cell {
                date: d.date.to_string(),
                day: d.date.day(),
                month: None,
                title: d.title.clone(),
                aria: format!(
                    "{weekday} {}, {}: {}, {status_text}",
                    short_date(d.date),
                    subject_name,
                    d.title
                ),
                subject_name,
                color: subject.map_or_else(|| "#6b7280".to_owned(), |s| s.color.clone()),
                emoji: subject.map_or_else(|| icon(&d.subject).to_owned(), |s| s.emoji.clone()),
                phase: phase_label(&d.phase),
                minutes: d.minutes,
                done,
                total,
                percent,
                fill: 30 + percent / 2,
                status: status.slug(),
                is_today: d.date == today,
                is_exam: d.phase == "exam",
            },
            d,
        ));
    }
    let (streak, record) = streaks(&flags, today);

    // Weeks run Monday to Sunday (the plan starts on a Monday).
    let mut weeks: Vec<Week> = Vec::new();
    let mut prev_phase: Option<&str> = None;
    for (n, chunk) in cells.chunks(7).enumerate() {
        let first = chunk[0].1;
        let last = chunk[chunk.len() - 1].1;
        let divider = match prev_phase {
            Some(p) if p != first.phase => Some(phase_label(&first.phase)),
            _ => None,
        };
        prev_phase = Some(first.phase.as_str());
        weeks.push(Week {
            label: format!(
                "Week {} · {} – {}",
                n + 1,
                short_date(first.date),
                short_date(last.date)
            ),
            divider,
            cells: Vec::new(),
        });
    }
    let mut last_month = None;
    for (n, (mut cell, d)) in cells.into_iter().enumerate() {
        let m = d.date.month();
        if last_month != Some(m) {
            cell.month = Some(MONTHS[d.date.month0() as usize]);
            last_month = Some(m);
        }
        weeks[n / 7].cells.push(cell);
    }

    let legend = subjects
        .iter()
        .map(|s| LegendSubject {
            name: s.name.clone(),
            emoji: s.emoji.clone(),
            color: s.color.clone(),
        })
        .collect();

    Ok(View::typed(PlanPage {
        title: "Plan",
        weeks,
        legend,
        streak,
        record,
        days_done,
        days_passed,
        days_total: plan.len() as i64,
        minutes_done,
        minutes_total,
        readonly,
    }))
}

/// One day: the Today page for any date. Past days can be ticked (forgot yesterday);
/// future days cannot (the checklist refuses).
async fn show(
    ctx: LiveContext,
    user: AuthUser,
    State(db): State<Db>,
    Path(date): Path<String>,
) -> Result<View> {
    let date = NaiveDate::parse_from_str(&date, "%Y-%m-%d").map_err(|_| Error::NotFound)?;
    today::day_view(ctx, &user, &db, date).await
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, 10, day).unwrap()
    }

    #[test]
    fn statuses() {
        assert_eq!(status_of(d(13), d(14), 12, 12), Status::Done);
        assert_eq!(status_of(d(13), d(14), 6, 12), Status::Partial);
        assert_eq!(status_of(d(13), d(14), 0, 12), Status::Missed);
        assert_eq!(status_of(d(14), d(14), 0, 12), Status::Pending);
        assert_eq!(status_of(d(15), d(14), 0, 12), Status::Future);
        assert_eq!(percent_of(6, 12), 50);
    }

    #[test]
    fn streak_rules() {
        // 12-15 done, 16 missed, 17-19 done, 20 not yet.
        let days: Vec<_> = (12..=20).map(|n| (d(n), n != 16 && n < 20)).collect();
        assert_eq!(streaks(&days, d(19)), (3, 4));
        // Today (20) not done: the streak runs up to yesterday.
        assert_eq!(streaks(&days, d(20)), (3, 4));
        assert_eq!(streaks(&days, d(17)).0, 1);
        assert_eq!(streaks(&days, d(16)).0, 4);
        assert_eq!(streaks(&days, d(18)).0, 2);
        assert_eq!(streaks(&days, d(11)), (0, 0));
    }
}
