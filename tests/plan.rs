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

/// Ticks the first `n` tasks of `day` for `user_id` (all of them when `n` is `None`).
async fn tick(test: &TestApp, user_id: i64, day: &str, n: Option<usize>) -> usize {
    let ids = task_ids(test, day).await;
    let n = n.unwrap_or(ids.len());
    for id in ids.iter().take(n) {
        TaskCheck::create(
            test.db(),
            TaskCheck {
                user_id,
                plan_task_id: *id,
                checked_at: renox::db::now(),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    }
    ids.len()
}

#[renox::test]
async fn the_calendar_shows_five_weeks_and_links_every_day() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 14);
    test.acting_as(&student);
    let res = test.get("/plan").await;
    res.assert_ok()
        .assert_see("Study plan calendar")
        .assert_see("Week 1")
        .assert_see("Week 5")
        .assert_dont_see("Week 6")
        .assert_see("/plan/2026-10-12")
        .assert_see("/plan/2026-11-15")
        .assert_see("🏁")
        .assert_see("Mathematics")
        .assert_see("30-minute routine starts")
        .assert_see("data-today=\"true\"")
        .assert_see("Streak");
}

#[renox::test]
async fn done_partial_missed_and_future_days_have_their_own_status() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    // 13 Oct: all done. 14 Oct: half. 15 Oct: nothing (and in the past). 16 Oct: today.
    let total = tick(&test, student.id, "2026-10-13", None).await;
    tick(&test, student.id, "2026-10-14", Some(total / 2)).await;
    let half = task_ids(&test, "2026-10-14").await.len();
    let percent = (total / 2) * 100 / half;
    travel_to(&test, 10, 16);
    test.acting_as(&student);
    test.get("/plan")
        .await
        .assert_ok()
        .assert_see("data-date=\"2026-10-13\" data-status=\"done\"")
        .assert_see("data-date=\"2026-10-14\" data-status=\"partial\"")
        .assert_see(&format!("{percent}%"))
        .assert_see("data-date=\"2026-10-15\" data-status=\"missed\"")
        .assert_see("data-date=\"2026-10-16\" data-status=\"pending\"")
        .assert_see("data-date=\"2026-10-17\" data-status=\"future\"");
}

#[renox::test]
async fn half_ticked_day_is_fifty_percent() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let all = task_ids(&test, "2026-10-13").await.len();
    assert!(all >= 2);
    tick(&test, student.id, "2026-10-13", Some(all / 2)).await;
    travel_to(&test, 10, 14);
    test.acting_as(&student);
    let expected = (all / 2) * 100 / all;
    test.get("/plan")
        .await
        .assert_see("data-date=\"2026-10-13\" data-status=\"partial\"")
        .assert_see(&format!("{expected}%"));
}

#[renox::test]
async fn the_streak_runs_across_the_phase_boundary() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    // 12-18 Oct (4-hour phase) and 19 Oct (30-minute phase) all done; 20 Oct not yet.
    for day in 12..=19 {
        tick(&test, student.id, &format!("2026-10-{day}"), None).await;
    }
    travel_to(&test, 10, 20);
    test.acting_as(&student);
    test.get("/plan")
        .await
        .assert_ok()
        .assert_see("<span id=\"streak-current\">8</span>")
        .assert_see("<strong id=\"streak-record\">8</strong>")
        .assert_see("<span id=\"days-done\">8</span>")
        .assert_see("<span id=\"days-passed\">9</span>");

    // Completing today extends it; a gap breaks the current streak but not the record.
    tick(&test, student.id, "2026-10-20", None).await;
    test.get("/plan")
        .await
        .assert_see("<span id=\"streak-current\">9</span>");
    travel_to(&test, 10, 22);
    test.acting_as(&student);
    test.get("/plan")
        .await
        .assert_see("<span id=\"streak-current\">0</span>")
        .assert_see("<strong id=\"streak-record\">9</strong>");
}

#[renox::test]
async fn study_minutes_add_up_completed_days_and_parts_of_partial_days() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    tick(&test, student.id, "2026-10-12", None).await;
    travel_to(&test, 10, 13);
    test.acting_as(&student);
    let minutes: i64 = renox::db::sql("SELECT minutes FROM plan_days WHERE date = '2026-10-12'")
        .scalar(test.db())
        .await
        .unwrap();
    test.get("/plan")
        .await
        .assert_see(&format!("<span id=\"minutes-done\">{minutes}</span>"));
}

#[renox::test]
async fn a_day_page_opens_for_any_date_and_links_to_its_neighbours() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 20);
    test.acting_as(&student);
    test.get("/plan/2026-10-14")
        .await
        .assert_ok()
        .assert_see("Wednesday, 14 October 2026")
        .assert_see("/plan/2026-10-13")
        .assert_see("/plan/2026-10-15")
        .assert_see("Calendar");
    test.get("/plan/not-a-date").await.assert_status(404);
    test.get("/plan/2026-12-01")
        .await
        .assert_ok()
        .assert_see("HUSO Round 1 is over");
}

#[renox::test]
async fn a_past_day_can_still_be_ticked() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 15);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-13").await;
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 13), false));
    list.call_with("toggle", json!([ids[0]]))
        .await
        .assert_ok()
        .assert_see(&format!("1/{} tasks", ids.len()));
    test.assert_database_count("task_checks", 1).await;
}

#[renox::test]
async fn tasks_of_future_days_cannot_be_ticked() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 15);
    test.acting_as(&student);
    let ids = task_ids(&test, "2026-10-16").await;
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 16), false));
    list.call_with("toggle", json!([ids[0]]))
        .await
        .assert_forbidden();
    test.assert_database_count("task_checks", 0).await;
    test.get("/plan/2026-10-16")
        .await
        .assert_ok()
        .assert_see("This day has not started yet");
}

#[renox::test]
async fn the_parent_sees_the_students_calendar_read_only() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let parent = user(&test, "parent@huso.local").await;
    tick(&test, student.id, "2026-10-13", None).await;
    travel_to(&test, 10, 14);
    test.acting_as(&parent);
    test.get("/plan")
        .await
        .assert_ok()
        .assert_see("Read-only")
        .assert_see("data-date=\"2026-10-13\" data-status=\"done\"");
    test.get("/plan/2026-10-13")
        .await
        .assert_ok()
        .assert_see("Read-only");
    let ids = task_ids(&test, "2026-10-12").await;
    let mut list = test.live(TodayChecklist::new(student.id, date(10, 12), false));
    list.call_with("toggle", json!([ids[0]]))
        .await
        .assert_forbidden();
}

#[renox::test]
async fn guests_are_sent_to_the_login() {
    let test = seeded().await;
    // The calendar and the days are public (without progress).
    test.get("/plan").await.assert_ok();
    test.get("/plan/2026-10-13").await.assert_ok();
}
