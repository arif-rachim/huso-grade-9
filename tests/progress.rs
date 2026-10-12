use huso::app;
use huso::app::content::models::{Question, Subject, Topic};
use huso::app::practice::models::{Answer, Attempt};
use huso::app::progress::models::ExternalLog;
use huso::app::progress::stats;
use renox::chrono::NaiveDate;
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;

async fn seeded() -> TestApp {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    // Noon in Jakarta on Tuesday 20 October 2026.
    let target = NaiveDate::from_ymd_opt(2026, 10, 20)
        .unwrap()
        .and_hms_opt(5, 0, 0)
        .unwrap()
        .and_utc();
    test.travel((target - renox::db::now()).to_std().expect("date is ahead"));
    test
}

async fn user(test: &TestApp, email: &str) -> User {
    User::find_by_email(test.db(), email)
        .await
        .unwrap()
        .unwrap()
}

fn date(month: u32, day: u32) -> NaiveDate {
    NaiveDate::from_ymd_opt(2026, month, day).unwrap()
}

/// Adds a log straight to the database.
#[allow(clippy::too_many_arguments)]
async fn log(
    test: &TestApp,
    user: &User,
    on: NaiveDate,
    source: &str,
    subject: &str,
    right: i64,
    wrong: i64,
    blank: i64,
    minutes: i64,
) -> ExternalLog {
    ExternalLog::create(
        test.db(),
        ExternalLog {
            user_id: user.id,
            date: on,
            source: source.into(),
            subject: subject.into(),
            correct: right,
            wrong,
            blank,
            minutes,
            ..Default::default()
        },
    )
    .await
    .unwrap()
}

async fn logs(test: &TestApp) -> Vec<ExternalLog> {
    ExternalLog::query()
        .order_by(ExternalLog::ID)
        .get(test.db())
        .await
        .unwrap()
}

#[renox::test]
async fn the_diagnostic_form_saves_one_log_per_subject_with_the_right_scores() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/progress/log")
        .await
        .assert_ok()
        .assert_see("all 5 subjects");

    let rows = [
        ("math", "6", "2", "4", "30"),
        ("physics", "15", "3", "2", "36"),
        ("chemistry", "14", "7", "14", "36"),
        ("biology", "30", "5", "5", "36"),
        ("earth", "36", "4", "5", "36"),
    ];
    let mut form: Vec<(String, String)> = vec![("date".into(), "2026-10-12".into())];
    for (i, (subject, right, wrong, blank, minutes)) in rows.iter().enumerate() {
        form.push((format!("rows[{i}][subject]"), (*subject).into()));
        form.push((format!("rows[{i}][correct]"), (*right).into()));
        form.push((format!("rows[{i}][wrong]"), (*wrong).into()));
        form.push((format!("rows[{i}][blank]"), (*blank).into()));
        form.push((format!("rows[{i}][minutes]"), (*minutes).into()));
    }
    let pairs: Vec<(&str, &str)> = form.iter().map(|(k, v)| (k.as_str(), v.as_str())).collect();
    test.post("/progress/log/diagnostic", &pairs)
        .await
        .assert_status(303);

    let saved = logs(&test).await;
    assert_eq!(saved.len(), 5);
    assert!(saved.iter().all(|l| l.source == "huso-2024-r1"));
    assert!(saved.iter().all(|l| l.user_id == student.id));
    assert!(saved.iter().all(|l| l.date == date(10, 12)));
    let chem = saved.iter().find(|l| l.subject == "chemistry").unwrap();
    assert_eq!(
        (chem.correct, chem.wrong, chem.blank, chem.minutes),
        (14, 7, 14, 36)
    );
    // raw_q = 4 * correct - wrong, shown as raw_q / 4.
    assert_eq!(chem.tally().raw_q(), 49);
    let page = test.get("/progress").await;
    page.assert_ok().assert_see("12.25").assert_see("40.0%");
}

#[renox::test]
async fn an_empty_diagnostic_row_is_skipped() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.post(
        "/progress/log/diagnostic",
        &[
            ("date", "2026-10-12"),
            ("rows[0][subject]", "math"),
            ("rows[0][correct]", "5"),
            ("rows[0][wrong]", "1"),
            ("rows[0][blank]", "0"),
            ("rows[1][subject]", "physics"),
            ("rows[1][correct]", ""),
        ],
    )
    .await
    .assert_status(303);
    assert_eq!(logs(&test).await.len(), 1);
}

#[renox::test]
async fn validation_checks_totals_numbers_and_dates() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    let base = |extra: &[(&'static str, &'static str)]| {
        let mut f = vec![
            ("date", "2026-10-20"),
            ("source", "huso-2024-r1"),
            ("subject", "math"),
            ("correct", "3"),
            ("wrong", "1"),
            ("blank", "0"),
        ];
        for (k, v) in extra {
            f.retain(|(key, _)| key != k);
            f.push((k, v));
        }
        f
    };
    test.htmx()
        .post(
            "/progress/log",
            &base(&[("correct", "0"), ("wrong", "0"), ("blank", "0")]),
        )
        .await
        .assert_invalid("correct");
    test.htmx()
        .post("/progress/log", &base(&[("wrong", "-2")]))
        .await
        .assert_invalid("wrong");
    test.htmx()
        .post("/progress/log", &base(&[("date", "2026-09-30")]))
        .await
        .assert_invalid("date");
    test.htmx()
        .post("/progress/log", &base(&[("date", "2026-12-01")]))
        .await
        .assert_invalid("date");
    test.htmx()
        .post("/progress/log", &base(&[("source", "")]))
        .await
        .assert_invalid("source");
    assert!(logs(&test).await.is_empty());

    test.post("/progress/log", &base(&[("minutes", "45")]))
        .await
        .assert_status(303);
    let saved = logs(&test).await;
    assert_eq!(saved.len(), 1);
    assert_eq!(
        (saved[0].correct, saved[0].wrong, saved[0].minutes),
        (3, 1, 45)
    );
}

#[renox::test]
async fn before_after_compares_the_diagnostic_with_the_latest_log_or_attempt() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    log(
        &test,
        &student,
        date(10, 12),
        "huso-2024-r1",
        "math",
        6,
        2,
        4,
        30,
    )
    .await;
    // A second diagnostic log is not the baseline; it is a later result.
    log(
        &test,
        &student,
        date(10, 15),
        "huso-2024-r1",
        "math",
        8,
        2,
        2,
        30,
    )
    .await;
    log(
        &test,
        &student,
        date(10, 12),
        "huso-2024-r1",
        "physics",
        18,
        0,
        0,
        36,
    )
    .await;
    log(
        &test,
        &student,
        date(10, 18),
        "amc10",
        "physics",
        9,
        1,
        0,
        40,
    )
    .await;
    log(
        &test,
        &student,
        date(10, 13),
        "amc10",
        "biology",
        5,
        5,
        0,
        20,
    )
    .await;

    // A finished math attempt on 19 Oct (23:30 UTC is already the 20th in Jakarta).
    let topic = Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .first(test.db())
        .await
        .unwrap();
    let subjects = Subject::query()
        .order_by(Subject::POSITION)
        .get(test.db())
        .await
        .unwrap();
    let math = subjects.iter().find(|s| s.slug == "math").unwrap();
    let sub = match topic {
        Some(t) if t.subject_id == math.id => t,
        _ => {
            let parent = Topic::create(
                test.db(),
                Topic {
                    slug: "math.t".into(),
                    subject_id: math.id,
                    name: "T".into(),
                    ..Default::default()
                },
            )
            .await
            .unwrap();
            Topic::create(
                test.db(),
                Topic {
                    slug: "math.t.s".into(),
                    subject_id: math.id,
                    parent_id: Some(parent.id),
                    name: "S".into(),
                    items: Json(vec![]),
                    ..Default::default()
                },
            )
            .await
            .unwrap()
        }
    };
    let q = Question::create(
        test.db(),
        Question {
            key: "progress-q1".into(),
            topic_id: sub.id,
            difficulty: 1,
            stem: "S".into(),
            answer: "A".into(),
            source: "original".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let finished = date(10, 19).and_hms_opt(23, 30, 0).unwrap().and_utc();
    let attempt = Attempt::create(
        test.db(),
        Attempt {
            user_id: student.id,
            mode: "mixed".into(),
            started_at: finished,
            finished_at: Some(finished),
            question_ids: Json(vec![q.id]),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    Answer::create(
        test.db(),
        Answer {
            attempt_id: attempt.id,
            question_id: q.id,
            position: 0,
            choice: Some("A".into()),
            is_correct: true,
            answered_at: Some(finished),
            ..Default::default()
        },
    )
    .await
    .unwrap();

    let data = stats::load(test.db(), student.id).await.unwrap();
    let rows = stats::before_after(&data.subjects, &data.entries);
    let row = |slug: &str| rows.iter().find(|r| r.slug == slug).unwrap().clone();
    // Math: diagnostic 6/12 = 50 %; latest is the attempt of the 20th (Jakarta), 1/1 = 100 %.
    assert_eq!(
        (row("math").before, row("math").after),
        (Some(50.0), Some(100.0))
    );
    // Physics: 100 % before, 9/10 = 90 % after.
    assert_eq!(
        (row("physics").before, row("physics").after),
        (Some(100.0), Some(90.0))
    );
    // Biology has no diagnostic; chemistry has nothing at all.
    assert_eq!(
        (row("biology").before, row("biology").after),
        (None, Some(50.0))
    );
    assert_eq!(
        (row("chemistry").before, row("chemistry").after),
        (None, None)
    );
    assert_eq!(row("math").color, "#2563eb");

    // The page draws the chart from the same data.
    test.acting_as(&student);
    test.get("/progress")
        .await
        .assert_ok()
        .assert_see("chart-before-after")
        .assert_see("Mathematics")
        .assert_see("Still missing a result for");
}

#[renox::test]
async fn the_simulation_keeps_the_best_four_and_names_the_dropped_subject() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    for (subject, right, wrong, blank) in [
        ("math", 6, 2, 4),
        ("physics", 15, 3, 2),
        ("chemistry", 14, 7, 14),
        ("biology", 30, 5, 5),
        ("earth", 36, 4, 5),
    ] {
        log(
            &test,
            &student,
            date(10, 16),
            "amc10",
            subject,
            right,
            wrong,
            blank,
            0,
        )
        .await;
    }
    let data = stats::load(test.db(), student.id).await.unwrap();
    let sim = stats::simulation(&data.subjects, &data.entries).expect("all five subjects");
    assert_eq!(sim.dropped.as_deref(), Some("Chemistry"));
    assert_eq!(sim.rows.iter().filter(|r| r.kept).count(), 4);
    assert_eq!(sim.total, "280.0");
    test.acting_as(&student);
    test.get("/progress")
        .await
        .assert_ok()
        .assert_see("Chemistry is dropped");
}

#[renox::test]
async fn totals_streak_and_minutes_come_from_logs_and_study_sessions() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    log(&test, &student, date(10, 19), "amc10", "math", 8, 2, 0, 25).await;
    log(&test, &student, date(10, 20), "amc10", "math", 5, 5, 0, 15).await;
    renox::db::sql("INSERT INTO study_sessions (user_id, date, minutes, subject, note) VALUES (?, '2026-10-20', 30, 'math', '')")
        .bind(student.id)
        .execute(test.db())
        .await
        .unwrap();
    let data = stats::load(test.db(), student.id).await.unwrap();
    assert_eq!(data.minutes[&date(10, 19)], 25);
    assert_eq!(data.minutes[&date(10, 20)], 45);
    let days = data.minutes.keys().copied().collect();
    assert_eq!(stats::streak(&days, date(10, 20)), 2);
    let per_day = stats::minutes_per_day(&data.minutes, &data.plan, date(10, 12), date(10, 20));
    assert_eq!(per_day.labels.len(), 9);
    assert_eq!(per_day.series[0].values[8], Some(45.0));
    // 12 Oct is an intensive day: 240 minutes wanted.
    assert_eq!(per_day.series[1].values[0], Some(240.0));
    let totals = stats::source_totals(&data.logs, |s| s.to_owned());
    assert_eq!(totals.len(), 1);
    assert_eq!(
        (totals[0].entries, totals[0].questions, totals[0].minutes),
        (2, 20, 40)
    );
    assert_eq!(totals[0].percent, "65.0");
    assert_eq!(totals[0].score, "11.25");

    test.acting_as(&student);
    test.get("/progress")
        .await
        .assert_ok()
        .assert_see("Totals per source")
        .assert_see("chart-minutes-day");
}

#[renox::test]
async fn the_page_runs_a_constant_number_of_queries() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    log(
        &test,
        &student,
        date(10, 12),
        "huso-2024-r1",
        "math",
        6,
        2,
        4,
        30,
    )
    .await;
    let (_, few) = renox::db::capture_queries(async { test.get("/progress").await.status }).await;
    for i in 0..20 {
        let subject = ["math", "physics", "chemistry", "biology", "earth"][i % 5];
        log(
            &test,
            &student,
            date(10, 13 + (i as u32 % 7)),
            "amc10",
            subject,
            5,
            2,
            1,
            20,
        )
        .await;
    }
    let (_, many) = renox::db::capture_queries(async { test.get("/progress").await.status }).await;
    assert_eq!(few.len(), many.len(), "{few:?} vs {many:?}");
}

#[renox::test]
async fn the_parent_reads_but_cannot_write() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let parent = user(&test, "parent@huso.local").await;
    let entry = log(&test, &student, date(10, 16), "amc10", "math", 8, 2, 0, 25).await;
    test.acting_as(&parent);
    test.get("/progress")
        .await
        .assert_ok()
        .assert_see("Read-only")
        .assert_see("amc10")
        .assert_dont_see("Log practice");
    test.get("/progress/log").await.assert_forbidden();
    test.get(&format!("/progress/log/{}/edit", entry.id))
        .await
        .assert_forbidden();
    test.post(
        "/progress/log",
        &[
            ("date", "2026-10-20"),
            ("source_other", "x"),
            ("subject", "math"),
            ("correct", "1"),
        ],
    )
    .await
    .assert_forbidden();
    test.delete(&format!("/progress/log/{}", entry.id))
        .await
        .assert_forbidden();
    assert_eq!(logs(&test).await.len(), 1);
}

#[renox::test]
async fn the_student_edits_and_deletes_an_entry() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let entry = log(&test, &student, date(10, 16), "amc10", "math", 8, 2, 0, 25).await;
    test.acting_as(&student);
    test.get(&format!("/progress/log/{}/edit", entry.id))
        .await
        .assert_ok()
        .assert_see("Edit practice log");
    test.put(
        &format!("/progress/log/{}", entry.id),
        &[
            ("date", "2026-10-17"),
            ("source_other", "AMC 10A 2023"),
            ("subject", "physics"),
            ("correct", "9"),
            ("wrong", "1"),
            ("blank", "0"),
            ("minutes", "40"),
            ("note", "Careful with units"),
        ],
    )
    .await
    .assert_status(303);
    let saved = logs(&test).await;
    assert_eq!(saved.len(), 1);
    assert_eq!(
        (
            saved[0].subject.as_str(),
            saved[0].source.as_str(),
            saved[0].correct,
            saved[0].date
        ),
        ("physics", "AMC 10A 2023", 9, date(10, 17))
    );
    test.get("/progress")
        .await
        .assert_see("AMC 10A 2023")
        .assert_see("Careful with units");

    test.delete(&format!("/progress/log/{}", entry.id))
        .await
        .assert_ok();
    assert!(logs(&test).await.is_empty());
}

#[renox::test]
async fn an_empty_page_works_without_any_data() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/progress")
        .await
        .assert_ok()
        .assert_see("No results yet")
        .assert_see("Nothing logged yet");
}
