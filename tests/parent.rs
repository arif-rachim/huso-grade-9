use huso::app;
use huso::app::content::models::{Question, Topic};
use huso::app::errors::models::ErrorEntry;
use huso::app::practice::models::{Answer, Attempt};
use huso::app::today::models::{StudySession, TaskCheck};
use renox::chrono::NaiveDate;
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;

/// Seeded app, with the clock at noon Jakarta time on Tuesday `2026-month-day`.
async fn seeded(month: u32, day: u32) -> TestApp {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    let target = date(month, day).and_hms_opt(5, 0, 0).unwrap().and_utc();
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

/// Ticks the first `n` tasks of a plan day (`n = None`: all of them) at noon Jakarta time.
async fn tick(test: &TestApp, student: &User, day: &str, n: Option<usize>) {
    let ids: Vec<i64> = renox::db::sql(
        "SELECT t.id FROM plan_tasks t JOIN plan_days d ON d.id = t.plan_day_id \
         WHERE d.date = ? ORDER BY t.position",
    )
    .bind(day)
    .scalars(test.db())
    .await
    .unwrap();
    let when = day
        .parse::<NaiveDate>()
        .unwrap()
        .and_hms_opt(5, 0, 0)
        .unwrap();
    for id in ids.into_iter().take(n.unwrap_or(usize::MAX)) {
        TaskCheck::create(
            test.db(),
            TaskCheck {
                user_id: student.id,
                plan_task_id: id,
                checked_at: when.and_utc(),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    }
}

async fn session(test: &TestApp, student: &User, on: NaiveDate, minutes: i64) {
    StudySession::create(
        test.db(),
        StudySession {
            user_id: student.id,
            date: on,
            minutes,
            subject: "math".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
}

async fn subtopic(test: &TestApp, nth: u64) -> Topic {
    Topic::query()
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::ID)
        .offset(nth)
        .first(test.db())
        .await
        .unwrap()
        .expect("a subtopic")
}

/// One attempt on `topic` with answers `(is_correct)` given on `on` (noon Jakarta).
async fn answers(test: &TestApp, student: &User, topic: &Topic, on: NaiveDate, results: &[bool]) {
    let at = on.and_hms_opt(5, 0, 0).unwrap().and_utc();
    let mut ids = Vec::new();
    for (i, _) in results.iter().enumerate() {
        let q = Question::create(
            test.db(),
            Question {
                key: format!("parent-{}-{}-{i}", topic.id, on),
                topic_id: topic.id,
                difficulty: 1,
                stem: "S".into(),
                answer: "A".into(),
                source: "original".into(),
                ..Default::default()
            },
        )
        .await
        .unwrap();
        ids.push(q.id);
    }
    let attempt = Attempt::create(
        test.db(),
        Attempt {
            user_id: student.id,
            mode: "mixed".into(),
            started_at: at,
            finished_at: Some(at),
            question_ids: Json(ids.clone()),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    for (i, ok) in results.iter().enumerate() {
        Answer::create(
            test.db(),
            Answer {
                attempt_id: attempt.id,
                question_id: ids[i],
                position: i as i64,
                choice: Some(if *ok { "A" } else { "B" }.into()),
                is_correct: *ok,
                answered_at: Some(at),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    }
}

async fn mistake(test: &TestApp, student: &User, topic: &Topic, cause: &str, n: i64) {
    ErrorEntry::create(
        test.db(),
        ErrorEntry {
            user_id: student.id,
            origin: "manual".into(),
            topic_id: topic.id,
            subject: "math".into(),
            cause: Some(cause.into()),
            note: Some(format!("note {n}")),
            due_on: date(10, 21),
            status: "open".into(),
            box_no: 1,
            ..Default::default()
        },
    )
    .await
    .unwrap();
}

#[renox::test]
async fn a_student_gets_403_and_a_guest_is_sent_to_login() {
    let test = seeded(10, 20).await;
    test.get("/parent").await.assert_redirect("/login");
    test.acting_as(&user(&test, "student@huso.local").await);
    test.get("/parent").await.assert_forbidden();
}

#[renox::test]
async fn the_page_has_no_form_that_posts() {
    let test = seeded(10, 20).await;
    test.acting_as(&user(&test, "parent@huso.local").await);
    let page = test.get("/parent").await;
    page.assert_ok().assert_see("Parent Dashboard");
    // The layout has a logout form in the account menu; the page itself must have none.
    let body = page.text();
    let main = body.split("<main").nth(1).expect("a main element");
    assert!(!main.contains("<form"), "no form inside the page");
    assert!(!main.contains("method=\"post\""));
    assert!(!main.contains("hx-post") && !main.contains("hx-put") && !main.contains("hx-delete"));
    // Quick links.
    page.assert_see("href=\"/progress\"")
        .assert_see("href=\"/syllabus\"")
        .assert_see("href=\"/errors\"")
        .assert_see("href=\"/today\"");
}

#[renox::test]
async fn the_numbers_are_computed_from_the_students_data() {
    let test = seeded(10, 20).await;
    let student = user(&test, "student@huso.local").await;
    // 12-18 Oct: only the 18th has study time. 19th fully ticked, 20th (today) partly.
    session(&test, &student, date(10, 18), 40).await;
    tick(&test, &student, "2026-10-19", None).await;
    tick(&test, &student, "2026-10-20", Some(1)).await;
    session(&test, &student, date(10, 19), 30).await;
    session(&test, &student, date(10, 13), 90).await; // before the 7-day window
    // Accuracy: 3 of 4 in the last 7 days (75.0 %); an old wrong answer does not count.
    let topic = subtopic(&test, 0).await;
    answers(
        &test,
        &student,
        &topic,
        date(10, 19),
        &[true, true, true, false],
    )
    .await;
    answers(&test, &student, &topic, date(10, 12), &[false]).await;

    test.acting_as(&user(&test, "parent@huso.local").await);
    let page = test.get("/parent").await;
    page.assert_ok()
        // streak 18, 19, 20 = 3 days
        .assert_see("3 days")
        // 1 full day of 9 elapsed (12-20 Oct)
        .assert_see("1 / 9")
        // 40 + 30 minutes in 14-20 Oct
        .assert_see(">70<")
        .assert_see("75.0%")
        .assert_see("1 of ")
        .assert_see("href=\"/today\"");
}

#[renox::test]
async fn it_lists_the_reddest_subtopics_and_the_five_latest_mistakes() {
    let test = seeded(10, 20).await;
    let student = user(&test, "student@huso.local").await;
    let weak = subtopic(&test, 0).await;
    let strong = subtopic(&test, 1).await;
    answers(&test, &student, &weak, date(10, 19), &[false, false, false]).await;
    answers(&test, &student, &strong, date(10, 19), &[true, true, true]).await;
    mistake(&test, &student, &weak, "concept", 1).await;
    for n in 2..=5 {
        mistake(&test, &student, &weak, "misread", n).await;
    }
    mistake(&test, &student, &strong, "rushed", 6).await;

    test.acting_as(&user(&test, "parent@huso.local").await);
    let page = test.get("/parent").await;
    page.assert_ok()
        .assert_see(&weak.name)
        .assert_see(&format!("/syllabus/{}", weak.slug))
        .assert_see("0%")
        .assert_see("100%")
        // 5 latest of 6: the first ("Concept") is dropped
        .assert_see("Rushed")
        .assert_see("Misread")
        .assert_dont_see("Concept");
}

#[renox::test]
async fn the_inactivity_warning_comes_and_goes() {
    let test = seeded(10, 20).await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&user(&test, "parent@huso.local").await);
    test.get("/parent")
        .await
        .assert_ok()
        .assert_see("No activity for 2 days");

    // Something done yesterday: no warning.
    session(&test, &student, date(10, 19), 20).await;
    test.get("/parent")
        .await
        .assert_ok()
        .assert_dont_see("No activity for 2 days");
}

#[renox::test]
async fn the_inactivity_warning_waits_until_the_plan_has_run_two_days() {
    let test = seeded(10, 13).await;
    test.acting_as(&user(&test, "parent@huso.local").await);
    test.get("/parent")
        .await
        .assert_ok()
        .assert_dont_see("No activity for 2 days");
}

#[renox::test]
async fn the_registration_reminder_ends_after_31_october() {
    let before = seeded(10, 31).await;
    before.acting_as(&user(&before, "parent@huso.local").await);
    before
        .get("/parent")
        .await
        .assert_ok()
        .assert_see("HUSO registration")
        .assert_see("issues/2");

    let after = seeded(11, 2).await;
    after.acting_as(&user(&after, "parent@huso.local").await);
    after
        .get("/parent")
        .await
        .assert_ok()
        .assert_dont_see("HUSO registration");
}

#[renox::test]
async fn the_query_count_does_not_grow_with_the_data() {
    let test = seeded(10, 20).await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&user(&test, "parent@huso.local").await);
    let topic = subtopic(&test, 0).await;
    answers(&test, &student, &topic, date(10, 19), &[true, false, false]).await;
    mistake(&test, &student, &topic, "concept", 1).await;
    let (_, few) = renox::db::capture_queries(async { test.get("/parent").await.status }).await;

    for i in 0..6 {
        let t = subtopic(&test, i).await;
        answers(
            &test,
            &student,
            &t,
            date(10, 18),
            &[true, false, false, true],
        )
        .await;
        mistake(&test, &student, &t, "rushed", i as i64).await;
        session(&test, &student, date(10, 14 + i as u32), 20).await;
        tick(&test, &student, &format!("2026-10-{}", 14 + i), Some(2)).await;
    }
    let (_, many) = renox::db::capture_queries(async { test.get("/parent").await.status }).await;
    assert_eq!(few.len(), many.len(), "{few:?} vs {many:?}");
}
