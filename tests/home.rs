use huso::app;
use renox::prelude::*;
use renox::testing::TestApp;
use std::time::Duration;

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

#[renox::test]
async fn login_page_is_english() {
    let test = TestApp::new(app()).await;
    test.get("/login").await.assert_ok().assert_see("Log in");
}

#[renox::test]
async fn seeding_twice_creates_exactly_two_users_with_roles() {
    let test = seeded().await;
    test.kernel().seed().await.unwrap();
    test.assert_database_count("users", 2).await;
    assert!(
        user(&test, "student@huso.local")
            .await
            .roles(test.db())
            .await
            .unwrap()
            .contains(&"student".to_owned())
    );
    assert!(
        user(&test, "parent@huso.local")
            .await
            .roles(test.db())
            .await
            .unwrap()
            .contains(&"parent".to_owned())
    );
}

#[renox::test]
async fn nobody_can_register() {
    let test = seeded().await;
    test.post(
        "/register",
        &[
            ("name", "Mallory"),
            ("email", "mallory@example.com"),
            ("password", "secret123"),
            ("password_confirmation", "secret123"),
        ],
    )
    .await
    .assert_status(405);
    test.assert_database_count("users", 2).await;
}

#[renox::test]
async fn logged_in_users_are_sent_to_today() {
    let test = seeded().await;
    test.get("/").await.assert_redirect("/login");
    test.acting_as(&user(&test, "student@huso.local").await);
    test.get("/").await.assert_redirect("/today");
}

#[renox::test]
async fn only_the_parent_sees_the_parent_link() {
    let test = seeded().await;
    test.acting_as(&user(&test, "student@huso.local").await);
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("Flashcards")
        .assert_dont_see("Parent");
    test.get("/parent").await.assert_forbidden();

    test.acting_as(&user(&test, "parent@huso.local").await);
    test.get("/today").await.assert_ok().assert_see("Parent");
    test.get("/parent").await.assert_ok();
}

#[renox::test]
async fn the_countdown_reaches_huso_day() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let until = |d: u32| -> Duration {
        // Noon Jakarta time on 2026-11-d, as seconds from the (possibly travelled) clock.
        let target = renox::chrono::NaiveDate::from_ymd_opt(2026, 11, d)
            .unwrap()
            .and_hms_opt(5, 0, 0)
            .unwrap()
            .and_utc();
        (target - renox::db::now())
            .to_std()
            .expect("test date is still ahead")
    };
    test.travel(until(14));
    test.acting_as(&student); // a session from before the trip would have expired
    test.get("/today")
        .await
        .assert_ok()
        .assert_see("D-1 to HUSO");
    test.travel(Duration::from_secs(24 * 60 * 60));
    test.acting_as(&student);
    test.get("/today").await.assert_ok().assert_see("HUSO day!");
}

#[renox::test]
async fn the_models_match_the_schema() {
    TestApp::new(app()).await.assert_models_match_schema().await;
}

#[renox::test]
async fn every_view_compiles() {
    TestApp::new(app()).await.assert_views_compile();
}
