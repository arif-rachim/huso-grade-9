//! Everything `/progress` shows, computed from a constant number of queries (5, however much
//! data there is). The calculations are plain functions on [`Entry`] values so they can be tested
//! without a database.

use super::models::{DIAGNOSTIC_SOURCE, ExternalLog};
use crate::app::content::models::Subject;
use crate::app::practice::scoring::{
    BestFour, SubjectScore, Tally, best_four, format_percent, format_quarters,
};
use renox::chrono::{Datelike, Duration, NaiveDate};
use renox::prelude::*;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet, HashMap};

/// Minutes per day wanted in the intensive phase and in the daily phase.
pub const TARGET_INTENSIVE: i64 = 240;
pub const TARGET_DAILY: i64 = 30;

/// One result of one subject: a finished practice attempt or a line of the practice log.
#[derive(Debug, Clone)]
pub struct Entry {
    pub date: NaiveDate,
    /// Tie-break for entries of the same day (a later one wins).
    pub seq: i64,
    pub subject: String,
    pub tally: Tally,
    /// The diagnostic: the first `huso-2024-r1` log of the subject.
    pub baseline: bool,
}

#[derive(Serialize, Debug, Clone, PartialEq)]
pub struct BeforeAfter {
    pub slug: String,
    pub name: String,
    pub color: String,
    /// Percent correct, one decimal; `None` when there is nothing yet.
    pub before: Option<f64>,
    pub after: Option<f64>,
}

#[derive(Serialize, Debug, Clone, PartialEq)]
pub struct SeriesOut {
    pub name: String,
    pub values: Vec<Option<f64>>,
}

#[derive(Serialize, Debug, Clone, Default, PartialEq)]
pub struct Bars {
    pub labels: Vec<String>,
    pub series: Vec<SeriesOut>,
}

fn pct(bp: i64) -> f64 {
    bp as f64 / 100.0
}

fn pct_of(t: &Tally) -> Option<f64> {
    (t.total() > 0).then(|| pct(t.percent_bp()))
}

fn add(a: Tally, b: Tally) -> Tally {
    Tally {
        correct: a.correct + b.correct,
        wrong: a.wrong + b.wrong,
        blank: a.blank + b.blank,
    }
}

/// The diagnostic of each subject (its first `huso-2024-r1` log).
pub fn baselines(entries: &[Entry]) -> HashMap<String, Tally> {
    entries
        .iter()
        .filter(|e| e.baseline)
        .map(|e| (e.subject.clone(), e.tally))
        .collect()
}

/// The most recent result of each subject, not counting the diagnostic itself.
pub fn latest(entries: &[Entry]) -> HashMap<String, Tally> {
    let mut best: HashMap<&str, &Entry> = HashMap::new();
    for e in entries
        .iter()
        .filter(|e| !e.baseline && e.tally.total() > 0)
    {
        let newer = best
            .get(e.subject.as_str())
            .is_none_or(|b| (e.date, e.seq) > (b.date, b.seq));
        if newer {
            best.insert(&e.subject, e);
        }
    }
    best.into_iter()
        .map(|(k, e)| (k.to_owned(), e.tally))
        .collect()
}

/// Diagnostic against latest, per subject.
pub fn before_after(subjects: &[Subject], entries: &[Entry]) -> Vec<BeforeAfter> {
    let (before, after) = (baselines(entries), latest(entries));
    subjects
        .iter()
        .map(|s| BeforeAfter {
            slug: s.slug.clone(),
            name: s.name.clone(),
            color: s.color.clone(),
            before: before.get(&s.slug).and_then(pct_of),
            after: after.get(&s.slug).and_then(pct_of),
        })
        .collect()
}

/// Everything ever done, per subject.
pub fn totals_by_subject(entries: &[Entry]) -> HashMap<String, Tally> {
    let mut map: HashMap<String, Tally> = HashMap::new();
    for e in entries {
        let t = map.entry(e.subject.clone()).or_default();
        *t = add(*t, e.tally);
    }
    map
}

/// The Monday of the week of `date`.
pub fn monday(date: NaiveDate) -> NaiveDate {
    date - Duration::days(i64::from(date.weekday().num_days_from_monday()))
}

/// Percent correct per week (labelled by its Monday), one series per subject; a week without
/// work in a subject is a gap (`None`).
pub fn weekly_trend(subjects: &[Subject], entries: &[Entry], today: NaiveDate) -> Bars {
    let Some(first) = entries.iter().map(|e| e.date).min() else {
        return Bars::default();
    };
    let last = entries
        .iter()
        .map(|e| e.date)
        .max()
        .unwrap_or(first)
        .max(today);
    let mut weeks = Vec::new();
    let mut w = monday(first);
    while w <= monday(last) {
        weeks.push(w);
        w += Duration::days(7);
    }
    let mut per: HashMap<(&str, NaiveDate), Tally> = HashMap::new();
    for e in entries {
        let t = per.entry((e.subject.as_str(), monday(e.date))).or_default();
        *t = add(*t, e.tally);
    }
    Bars {
        labels: weeks.iter().map(|w| w.to_string()).collect(),
        series: subjects
            .iter()
            .map(|s| SeriesOut {
                name: s.name.clone(),
                values: weeks
                    .iter()
                    .map(|w| per.get(&(s.slug.as_str(), *w)).and_then(pct_of))
                    .collect(),
            })
            .collect(),
    }
}

/// Minutes wanted on a plan day.
pub fn target_for(phase: Option<&str>, planned: Option<i64>) -> i64 {
    match phase {
        Some("intensive") => TARGET_INTENSIVE,
        Some("daily") => TARGET_DAILY,
        _ => planned.unwrap_or(TARGET_DAILY),
    }
}

/// Minutes studied per day, with the target, from the first day of the plan (or of the first
/// study) up to today. `minutes` and `plan` are keyed by date.
pub fn minutes_per_day(
    minutes: &BTreeMap<NaiveDate, i64>,
    plan: &BTreeMap<NaiveDate, (String, i64)>,
    plan_start: NaiveDate,
    today: NaiveDate,
) -> Bars {
    let start = minutes
        .keys()
        .next()
        .copied()
        .map_or(plan_start, |d| d.min(plan_start));
    let end = minutes
        .keys()
        .next_back()
        .copied()
        .map_or(today, |d| d.max(today));
    if end < start {
        return Bars::default();
    }
    let mut labels = Vec::new();
    let (mut studied, mut target) = (Vec::new(), Vec::new());
    let mut day = start;
    while day <= end {
        labels.push(day.to_string());
        studied.push(Some(minutes.get(&day).copied().unwrap_or(0) as f64));
        let p = plan.get(&day);
        target.push(Some(
            target_for(p.map(|p| p.0.as_str()), p.map(|p| p.1)) as f64
        ));
        day += Duration::days(1);
    }
    Bars {
        labels,
        series: vec![
            SeriesOut {
                name: "Minutes studied".into(),
                values: studied,
            },
            SeriesOut {
                name: "Target".into(),
                values: target,
            },
        ],
    }
}

/// Minutes per week (labelled by the Monday), from the first study to this week.
pub fn minutes_per_week(minutes: &BTreeMap<NaiveDate, i64>, today: NaiveDate) -> Bars {
    let Some(first) = minutes.keys().next().copied() else {
        return Bars::default();
    };
    let mut per: BTreeMap<NaiveDate, i64> = BTreeMap::new();
    let mut w = monday(first);
    while w <= monday(today) {
        per.insert(w, 0);
        w += Duration::days(7);
    }
    for (d, m) in minutes {
        *per.entry(monday(*d)).or_default() += m;
    }
    Bars {
        labels: per.keys().map(|d| d.to_string()).collect(),
        series: vec![SeriesOut {
            name: "Minutes per week".into(),
            values: per.values().map(|m| Some(*m as f64)).collect(),
        }],
    }
}

/// Days in a row (ending today, or yesterday if today has no study yet) with some study.
pub fn streak(days: &BTreeSet<NaiveDate>, today: NaiveDate) -> i64 {
    let mut day = if days.contains(&today) {
        today
    } else {
        today - Duration::days(1)
    };
    let mut n = 0;
    while days.contains(&day) {
        n += 1;
        day -= Duration::days(1);
    }
    n
}

#[derive(Serialize, Debug, Clone)]
pub struct SimRow {
    pub name: String,
    pub color: String,
    pub percent: String,
    pub score: String,
    pub kept: bool,
}

#[derive(Serialize, Debug, Clone)]
pub struct Simulation {
    pub rows: Vec<SimRow>,
    pub total: String,
    pub dropped: Option<String>,
}

/// The HUSO rule on the latest result of each subject: the best four count, one is dropped.
/// `None` until every subject has a result.
pub fn simulation(subjects: &[Subject], entries: &[Entry]) -> Option<Simulation> {
    let latest = latest(entries);
    let scores: Vec<SubjectScore> = subjects
        .iter()
        .filter_map(|s| {
            latest.get(&s.slug).map(|t| SubjectScore {
                slug: s.slug.clone(),
                tally: *t,
            })
        })
        .collect();
    if subjects.is_empty() || scores.len() < subjects.len() {
        return None;
    }
    let BestFour {
        kept,
        dropped,
        total_bp,
    } = best_four(&scores);
    let rows = kept
        .iter()
        .chain(dropped.iter())
        .map(|&i| {
            let s = &subjects[i];
            let t = scores[i].tally;
            SimRow {
                name: s.name.clone(),
                color: s.color.clone(),
                percent: format_percent(t.percent_bp()),
                score: format_quarters(t.raw_q()),
                kept: dropped != Some(i),
            }
        })
        .collect();
    Some(Simulation {
        rows,
        total: format_percent(total_bp),
        dropped: dropped.map(|i| subjects[i].name.clone()),
    })
}

/// Totals of one source of the practice log.
#[derive(Serialize, Debug, Clone, PartialEq)]
pub struct SourceTotal {
    pub source: String,
    pub entries: i64,
    pub questions: i64,
    pub percent: String,
    pub score: String,
    pub minutes: i64,
}

/// Per-source totals of the log, biggest first.
pub fn source_totals(logs: &[ExternalLog], title: impl Fn(&str) -> String) -> Vec<SourceTotal> {
    let mut map: BTreeMap<&str, (i64, Tally, i64)> = BTreeMap::new();
    for l in logs {
        let e = map.entry(l.source.as_str()).or_default();
        e.0 += 1;
        e.1 = add(e.1, l.tally());
        e.2 += l.minutes;
    }
    let mut out: Vec<SourceTotal> = map
        .into_iter()
        .map(|(source, (entries, t, minutes))| SourceTotal {
            source: title(source),
            entries,
            questions: t.total(),
            percent: format_percent(t.percent_bp()),
            score: format_quarters(t.raw_q()),
            minutes,
        })
        .collect();
    out.sort_by(|a, b| b.questions.cmp(&a.questions).then(a.source.cmp(&b.source)));
    out
}

/// All the numbers of the page.
pub struct Stats {
    pub subjects: Vec<Subject>,
    pub logs: Vec<ExternalLog>,
    pub entries: Vec<Entry>,
    pub minutes: BTreeMap<NaiveDate, i64>,
    pub plan: BTreeMap<NaiveDate, (String, i64)>,
    pub cards_mastered: i64,
}

/// Loads the student's data: subjects, the log, finished attempts per subject, study minutes,
/// the plan's phases and the mastered cards (5 queries).
pub async fn load(db: &Db, user_id: i64) -> Result<Stats> {
    let subjects = Subject::query().order_by(Subject::POSITION).get(db).await?;
    let logs = ExternalLog::query()
        .where_(ExternalLog::USER_ID.eq(user_id))
        .order_by(ExternalLog::DATE)
        .order_by(ExternalLog::ID)
        .get(db)
        .await?;
    // Correct, wrong and blank answers of every finished attempt, per subject.
    let rows: Vec<(i64, String, String, i64, i64, i64)> = renox::db::sql(
        "SELECT a.id, date(a.finished_at, '+7 hours'), s.slug, \
                SUM(ans.is_correct), \
                SUM(CASE WHEN ans.choice IS NOT NULL AND ans.is_correct = 0 THEN 1 ELSE 0 END), \
                SUM(CASE WHEN ans.choice IS NULL THEN 1 ELSE 0 END) \
         FROM attempts a \
         JOIN answers ans ON ans.attempt_id = a.id \
         JOIN questions q ON q.id = ans.question_id \
         JOIN topics t ON t.id = q.topic_id \
         JOIN subjects s ON s.id = t.subject_id \
         WHERE a.user_id = ? AND a.finished_at IS NOT NULL \
         GROUP BY a.id, s.slug",
    )
    .bind(user_id)
    .fetch_as(db)
    .await?;
    let sessions: Vec<(String, i64)> = renox::db::sql(
        "SELECT date, SUM(minutes) FROM study_sessions WHERE user_id = ? GROUP BY date",
    )
    .bind(user_id)
    .fetch_as(db)
    .await?;
    let plan_rows: Vec<(String, String, i64)> =
        renox::db::sql("SELECT date, phase, minutes FROM plan_days")
            .fetch_as(db)
            .await?;
    let cards_mastered: i64 =
        renox::db::sql("SELECT COUNT(*) FROM card_states WHERE user_id = ? AND box >= 4")
            .bind(user_id)
            .scalar(db)
            .await?;

    let mut entries = Vec::new();
    let mut seen: BTreeSet<&str> = BTreeSet::new();
    for l in &logs {
        let baseline = l.source == DIAGNOSTIC_SOURCE && seen.insert(l.subject.as_str());
        entries.push(Entry {
            date: l.date,
            seq: l.id,
            subject: l.subject.clone(),
            tally: l.tally(),
            baseline,
        });
    }
    for (id, date, slug, correct, wrong, blank) in rows {
        if let Ok(date) = date.parse() {
            entries.push(Entry {
                date,
                seq: 1_000_000 + id,
                subject: slug,
                tally: Tally {
                    correct,
                    wrong,
                    blank,
                },
                baseline: false,
            });
        }
    }
    let mut minutes: BTreeMap<NaiveDate, i64> = BTreeMap::new();
    for (d, m) in sessions {
        if let Ok(d) = d.parse() {
            *minutes.entry(d).or_default() += m;
        }
    }
    for l in &logs {
        if l.minutes > 0 {
            *minutes.entry(l.date).or_default() += l.minutes;
        }
    }
    let plan = plan_rows
        .into_iter()
        .filter_map(|(d, phase, m)| d.parse().ok().map(|d| (d, (phase, m))))
        .collect();
    Ok(Stats {
        subjects,
        logs,
        entries,
        minutes,
        plan,
        cards_mastered,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(m: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, m, day).unwrap()
    }

    fn entry(date: NaiveDate, seq: i64, subject: &str, c: i64, base: bool) -> Entry {
        Entry {
            date,
            seq,
            subject: subject.into(),
            tally: Tally {
                correct: c,
                wrong: 1,
                blank: 0,
            },
            baseline: base,
        }
    }

    #[test]
    fn latest_skips_the_diagnostic_and_takes_the_newest() {
        let entries = [
            entry(d(10, 12), 1, "math", 6, true),
            entry(d(10, 20), 2, "math", 8, false),
            entry(d(10, 25), 3, "math", 10, false),
            entry(d(10, 25), 1_000_001, "math", 3, false),
        ];
        assert_eq!(
            latest(&entries)["math"].correct,
            3,
            "same day: the later seq wins"
        );
        assert_eq!(baselines(&entries)["math"].correct, 6);
    }

    #[test]
    fn streak_counts_back_from_today_or_yesterday() {
        let days: BTreeSet<_> = [d(10, 10), d(10, 11), d(10, 12)].into();
        assert_eq!(streak(&days, d(10, 12)), 3);
        assert_eq!(streak(&days, d(10, 13)), 3);
        assert_eq!(streak(&days, d(10, 14)), 0);
    }

    #[test]
    fn targets_follow_the_phase() {
        assert_eq!(target_for(Some("intensive"), Some(200)), 240);
        assert_eq!(target_for(Some("daily"), Some(45)), 30);
        assert_eq!(target_for(Some("weekend"), Some(90)), 90);
        assert_eq!(target_for(None, None), 30);
    }

    #[test]
    fn weeks_start_on_monday() {
        assert_eq!(monday(d(10, 14)), d(10, 12));
        assert_eq!(monday(d(10, 18)), d(10, 12));
        assert_eq!(monday(d(10, 19)), d(10, 19));
    }
}
