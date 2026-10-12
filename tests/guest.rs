//! Guests (not logged in) can browse and study; login is only needed to answer or save.

use huso::app;
use huso::app::today::TodayChecklist;
use renox::chrono::NaiveDate;
use renox::prelude::*;
use renox::testing::TestApp;

const LESSON: &str = "biology.anatomy.nervous";

async fn user(test: &TestApp, email: &str) -> User {
    User::find_by_email(test.db(), email)
        .await
        .unwrap()
        .unwrap()
}

/// Moves the clock to noon Jakarta time on 13 October 2026 (a plan day).
fn travel_to_plan_day(test: &TestApp) {
    let target = NaiveDate::from_ymd_opt(2026, 10, 13)
        .unwrap()
        .and_hms_opt(5, 0, 0)
        .unwrap()
        .and_utc();
    test.travel((target - renox::db::now()).to_std().expect("date is ahead"));
}

/// An app where the student has ticked a task, drawn a lesson and checked it with wrong
/// answers; the test then continues as a guest.
async fn with_student_data() -> TestApp {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    travel_to_plan_day(&test);
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    let task: i64 = renox::db::sql(
        "SELECT t.id FROM plan_tasks t JOIN plan_days d ON d.id = t.plan_day_id \
         WHERE d.date = '2026-10-13' ORDER BY t.position LIMIT 1",
    )
    .scalar(test.db())
    .await
    .unwrap();
    let date = NaiveDate::from_ymd_opt(2026, 10, 13).unwrap();
    test.live(TodayChecklist::new(student.id, date, false))
        .call_with("toggle", json!([task]))
        .await
        .assert_ok();
    test.post(&format!("/lessons/{LESSON}/drawn"), &[("drawn", "true")])
        .await
        .assert_status(303);
    test.post(&format!("/lessons/{LESSON}/check"), &[("q1", "A")])
        .await
        .assert_status(303);
    // The student sees their own data, so the guest assertions below mean something.
    test.get(&format!("/lessons/{LESSON}"))
        .await
        .assert_ok()
        .assert_see("Last try")
        .assert_see("Drawn from memory");
    test.get("/today").await.assert_see("1/");
    test.logout();
    test
}

#[renox::test]
async fn the_home_page_sends_guests_to_today() {
    let test = TestApp::new(app()).await;
    test.get("/").await.assert_redirect("/today");
}

#[renox::test]
async fn a_guest_sees_the_public_pages_without_any_student_data() {
    let test = with_student_data().await;

    test.get("/today")
        .await
        .assert_ok()
        .assert_see("Tuesday, 13 October 2026")
        .assert_see("Log in to tick off tasks and save your progress")
        .assert_see("New material today")
        .assert_dont_see("tasks</strong>")
        .assert_dont_see("Flashcards due")
        .assert_dont_see("Error log due");
    test.get("/plan")
        .await
        .assert_ok()
        .assert_see("Log in to tick off tasks and save your progress")
        .assert_dont_see("Streak")
        .assert_dont_see("Days completed")
        .assert_dont_see("data-status=\"done\"")
        .assert_dont_see("data-status=\"partial\"");
    test.get("/plan/2026-10-13")
        .await
        .assert_ok()
        .assert_see("Tuesday, 13 October 2026")
        .assert_see("Log in to tick off tasks and save your progress")
        .assert_dont_see("tasks</strong>");
    test.get("/lessons")
        .await
        .assert_ok()
        .assert_see("Nervous System")
        .assert_dont_see("Not drawn")
        .assert_dont_see("Check: ");
    test.get(&format!("/lessons/{LESSON}"))
        .await
        .assert_ok()
        .assert_see("Check your understanding")
        .assert_see("Log in to check my answers")
        .assert_see("Log in to save")
        .assert_dont_see("Last try")
        .assert_dont_see("Drawn from memory")
        .assert_dont_see("Best check");
    test.get("/syllabus")
        .await
        .assert_ok()
        .assert_see("data-band=\"grey\"")
        .assert_dont_see("data-band=\"red\"")
        .assert_dont_see("data-band=\"yellow\"")
        .assert_dont_see("data-band=\"green\"");
    test.get(&format!("/syllabus/{LESSON}"))
        .await
        .assert_ok()
        .assert_see("Log in to practise this subtopic")
        .assert_dont_see("Open mistakes");
    test.get("/flashcards")
        .await
        .assert_ok()
        .assert_see("Log in to start review")
        .assert_dont_see("Due today")
        .assert_dont_see("Cards you made");
    test.get("/practice")
        .await
        .assert_ok()
        .assert_see("Log in to start a sprint")
        .assert_dont_see("Recent practices");
}

#[renox::test]
async fn gated_pages_and_actions_send_a_guest_to_the_login() {
    let test = with_student_data().await;
    for path in [
        "/flashcards/review",
        "/flashcards/manual/new",
        "/errors",
        "/errors/review",
        "/progress",
        "/progress/log",
        "/parent",
        "/redraw",
        "/redraw/biology.anatomy.nervous",
        "/account",
        "/practice/1",
        "/practice/1/result",
    ] {
        test.get(path).await.assert_redirect("/login");
    }
    test.post("/practice", &[("mode", "mixed")])
        .await
        .assert_redirect("/login");
    test.post("/practice/1/answer", &[("choice", "A")])
        .await
        .assert_redirect("/login");
    test.post(&format!("/lessons/{LESSON}/check"), &[("q1", "A")])
        .await
        .assert_redirect("/login");
    test.post(&format!("/lessons/{LESSON}/drawn"), &[("drawn", "true")])
        .await
        .assert_redirect("/login");
}

#[renox::test]
async fn after_logging_in_a_guest_returns_to_the_lesson_they_were_on() {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    // The lesson's own "Log in" button explains why and remembers the page.
    let button = format!("/log-in-first?next=%2Flessons%2F{LESSON}&why=answer");
    test.get(&button).await.assert_redirect("/login");
    test.get("/login")
        .await
        .assert_ok()
        .assert_see("Log in to answer questions and save your progress");
    test.post(
        "/login",
        &[("email", "student@huso.local"), ("password", "study123")],
    )
    .await
    .assert_redirect(&format!("/lessons/{LESSON}"));

    // A plain link to a gated page works the same way.
    test.logout();
    test.get("/errors").await.assert_redirect("/login");
    test.post(
        "/login",
        &[("email", "student@huso.local"), ("password", "study123")],
    )
    .await
    .assert_redirect("/errors");
}

#[renox::test]
async fn the_login_button_never_redirects_off_site() {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    test.get("/log-in-first?next=https%3A%2F%2Fevil.example%2F")
        .await
        .assert_redirect("/login");
    test.get("/log-in-first?next=%2F%2Fevil.example")
        .await
        .assert_redirect("/login");
    test.post(
        "/login",
        &[("email", "student@huso.local"), ("password", "study123")],
    )
    .await
    .assert_redirect("/");
}

#[renox::test]
async fn the_guest_navbar_has_the_study_links_and_a_login_button_but_no_personal_ones() {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("href=\"/plan\"")
        .assert_see("href=\"/lessons\"")
        .assert_see("href=\"/flashcards\"")
        .assert_see("href=\"/practice\"")
        .assert_see("href=\"/syllabus\"")
        .assert_see("Log in")
        .assert_see("to HUSO")
        .assert_dont_see("href=\"/errors\"")
        .assert_dont_see("href=\"/progress\"")
        .assert_dont_see("href=\"/parent\"");
    // The login page itself still works (and has no second login button in the bar).
    test.get("/login").await.assert_ok().assert_see("Log in");
}

#[renox::test]
async fn logged_in_users_keep_their_navbar_and_today_page() {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    travel_to_plan_day(&test);
    test.acting_as(&user(&test, "student@huso.local").await);
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("href=\"/errors\"")
        .assert_see("href=\"/progress\"")
        .assert_see("Flashcards due")
        .assert_see("0/")
        .assert_dont_see("Log in to tick off tasks")
        .assert_dont_see("id=\"nav-login\"");
    test.acting_as(&user(&test, "parent@huso.local").await);
    test.get("/parent").await.assert_ok();
}
