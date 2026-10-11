use huso::app;
use huso::app::today::TodayChecklist;
use huso::app::today::models::TaskCheck;
use renox::chrono::NaiveDate;
use renox::prelude::*;
use renox::testing::TestApp;

async fn seeded() -> TestApp {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    test
}

async fn user(test: &TestApp, email: &str) -> User {
    User::find_by_email(test.db(), email)
        .await
        .unwrap()
        .unwrap()
}

/// Moves the clock to noon Jakarta time on `2026-month-day`.
fn travel_to(test: &TestApp, month: u32, day: u32) {
    let target = NaiveDate::from_ymd_opt(2026, month, day)
        .unwrap()
        .and_hms_opt(5, 0, 0)
        .unwrap()
        .and_utc();
    test.travel((target - renox::db::now()).to_std().expect("date is ahead"));
}

fn date(month: u32, day: u32) -> NaiveDate {
    NaiveDate::from_ymd_opt(2026, month, day).unwrap()
}

/// The ids of the tasks of a plan day, in order.
async fn task_ids(test: &TestApp, day: &str) -> Vec<i64> {
    renox::db::sql(
        "SELECT t.id FROM plan_tasks t JOIN plan_days d ON d.id = t.plan_day_id \
         WHERE d.date = ? ORDER BY t.position",
    )
    .bind(day)
    .scalars(test.db())
    .await
    .unwrap()
}

#[renox::test]
async fn shows_the_day_of_the_plan_with_blocks_and_subject_colour() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let total = task_ids(&test, "2026-10-13").await.len();
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("Tuesday, 13 October 2026")
        .assert_see("Mathematics")
        .assert_see("Algebra, Number Theory")
        .assert_see("#2563eb")
        .assert_see("Intensive 4-hour holiday")
        .assert_see("issues/4")
        .assert_see(&format!("0/{total} tasks"))
        .assert_see("Block 1")
        .assert_see("Block 2")
        .assert_see("Block 3")
        .assert_see("Block 4")
        .assert_dont_see("Block 5")
        .assert_see("minutes")
        .assert_see("New material today")
        .assert_see("Polynomials")
        .assert_see("Flashcards due")
        .assert_see("Error log due");
}

#[renox::test]
async fn ticking_twice_creates_then_deletes_the_check_and_counts_progress() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-13").await;
    let total = ids.len();

    let mut list = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    list.call_with("toggle", json!([ids[0]]))
        .await
        .assert_ok()
        .assert_see(&format!("1/{total} tasks"));
    test.assert_database_count("task_checks", 1).await;
    let row = TaskCheck::query()
        .where_(TaskCheck::PLAN_TASK_ID.eq(ids[0]))
        .first(test.db())
        .await
        .unwrap()
        .unwrap();
    assert_eq!(row.user_id, student.id);

    list.call_with("toggle", json!([ids[1]]))
        .await
        .assert_see(&format!("2/{total} tasks"));
    list.call_with("toggle", json!([ids[0]]))
        .await
        .assert_see(&format!("1/{total} tasks"));
    test.assert_database_count("task_checks", 1).await;

    // A task of another day is refused.
    let other = task_ids(&test, "2026-10-14").await;
    list.call_with("toggle", json!([other[0]]))
        .await
        .assert_status(404);
    test.assert_database_count("task_checks", 1).await;
}

#[renox::test]
async fn the_page_shows_the_ticked_tasks() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-13").await;
    let total = ids.len();
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    list.call_with("toggle", json!([ids[0]])).await.assert_ok();
    test.get("/today")
        .await
        .assert_ok()
        .assert_see(&format!("1/{total} tasks"));
}

#[renox::test]
async fn ticking_everything_shows_the_toast_and_records_the_day() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-13").await;
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    for (i, id) in ids.iter().enumerate() {
        let r = list.call_with("toggle", json!([id])).await;
        r.assert_ok();
        if i + 1 < ids.len() {
            r.assert_dont_see("Today is done");
        } else {
            r.assert_see("Today is done!");
        }
    }
    test.assert_database_count("study_sessions", 1).await;
    // Unticking one takes the record back.
    list.call_with("toggle", json!([ids[0]])).await.assert_ok();
    test.assert_database_count("study_sessions", 0).await;
    // Ticking it again records the day once more (never twice).
    list.call_with("toggle", json!([ids[0]])).await.assert_ok();
    test.assert_database_count("study_sessions", 1).await;
}

#[renox::test]
async fn the_parent_sees_the_checklist_but_cannot_change_it() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let parent = user(&test, "parent@huso.local").await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-13").await;
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    list.call_with("toggle", json!([ids[0]])).await.assert_ok();

    test.acting_as(&parent);
    let total = ids.len();
    test.get("/today")
        .await
        .assert_ok()
        .assert_see(&format!("1/{total} tasks"))
        .assert_see("Read-only");
    // Even with a snapshot that claims to be writable, the actions are refused.
    let mut forged = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    forged
        .call_with("toggle", json!([ids[1]]))
        .await
        .assert_forbidden();
    let mut readonly = test.live(TodayChecklist::new(student.id, date(10, 13), true));
    readonly
        .call_with("toggle", json!([ids[1]]))
        .await
        .assert_forbidden();
    test.assert_database_count("task_checks", 1).await;
}

#[renox::test]
async fn outside_the_plan_shows_an_empty_message() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/today?date=2026-10-01")
        .await
        .assert_ok()
        .assert_see("The plan starts on 12 October");
    test.get("/today?date=2026-11-20")
        .await
        .assert_ok()
        .assert_see("HUSO Round 1 is over");

    travel_to(&test, 11, 20);
    test.acting_as(&student);
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("HUSO Round 1 is over");
}

#[renox::test]
async fn days_can_be_browsed_with_the_date_query() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/today?date=2026-10-14")
        .await
        .assert_ok()
        .assert_see("Wednesday, 14 October 2026")
        .assert_see("/plan/2026-10-13")
        .assert_see("/plan/2026-10-15");
    // A bad date falls back to today.
    test.get("/today?date=nonsense").await.assert_ok();
}

#[renox::test]
async fn non_subject_days_get_a_grey_chip() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/today?date=2026-10-12")
        .await
        .assert_ok()
        .assert_see("Setup + Diagnostic Test")
        .assert_see("#6b7280")
        .assert_see("Diagnostic");
}

#[renox::test]
async fn the_side_cards_count_what_is_due() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    huso::app::today::summary::flashcards_due(test.db(), student.id)
        .await
        // Nothing was reviewed yet: only the capped number of new cards is due.
        .map(|n| assert!((0..=20).contains(&n), "{n}"))
        .unwrap();
    huso::app::today::summary::errors_due(test.db(), student.id)
        .await
        .map(|n| assert_eq!(n, 0))
        .unwrap();
}

#[renox::test]
async fn guests_are_sent_to_the_login() {
    let test = seeded().await;
    test.get("/today").await.assert_redirect("/login");
}
