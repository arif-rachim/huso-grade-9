use huso::app;
use huso::app::content::files::load_all;
use huso::app::content::lesson_file::parse_lesson;
use huso::app::content::models::{Lesson, Topic};
use huso::app::lessons::LessonCheck;
use renox::chrono::NaiveDate;
use renox::prelude::*;
use renox::testing::TestApp;

const NERVOUS: &str = "biology.anatomy.nervous";
const MATH_POLY: &str = "math.algebra.polynomials";

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

async fn topic(test: &TestApp, slug: &str) -> Topic {
    Topic::query()
        .where_(Topic::SLUG.eq(slug))
        .first(test.db())
        .await
        .unwrap()
        .unwrap()
}

/// The right letters of a lesson, as the form fields `q1`..`q5`; `wrong` of them are made wrong.
async fn answers(test: &TestApp, slug: &str, wrong: usize) -> Vec<(String, String)> {
    let lesson = Lesson::query()
        .where_(Lesson::TOPIC_ID.eq(topic(test, slug).await.id))
        .first(test.db())
        .await
        .unwrap()
        .unwrap();
    parse_lesson(&lesson.markdown)
        .questions
        .iter()
        .enumerate()
        .map(|(i, q)| {
            let letter = if i < wrong {
                if q.answer == "A" { "B" } else { "A" }
            } else {
                q.answer.as_str()
            };
            (format!("q{}", q.number), letter.to_owned())
        })
        .collect()
}

async fn submit_check(test: &TestApp, slug: &str, wrong: usize) {
    let fields = answers(test, slug, wrong).await;
    let refs: Vec<(&str, &str)> = fields
        .iter()
        .map(|(k, v)| (k.as_str(), v.as_str()))
        .collect();
    test.post(&format!("/lessons/{slug}/check"), &refs)
        .await
        .assert_status(303);
}

async fn mark_drawn(test: &TestApp, slug: &str, drawn: bool) {
    test.post(
        &format!("/lessons/{slug}/drawn"),
        &[("drawn", if drawn { "true" } else { "false" })],
    )
    .await
    .assert_status(303);
}

#[renox::test]
async fn every_material_file_is_imported_and_a_second_import_changes_nothing() {
    let test = seeded().await;
    let files = load_all(std::path::Path::new(env!("CARGO_MANIFEST_DIR")))
        .unwrap()
        .lessons;
    assert!(files.len() >= 40, "{} lesson files", files.len());
    assert_eq!(
        Lesson::query().count(test.db()).await.unwrap() as usize,
        files.len()
    );
    test.kernel().seed().await.unwrap();
    assert_eq!(
        Lesson::query().count(test.db()).await.unwrap() as usize,
        files.len()
    );
    let lesson = Lesson::query()
        .where_(Lesson::TOPIC_ID.eq(topic(&test, NERVOUS).await.id))
        .first(test.db())
        .await
        .unwrap()
        .unwrap();
    assert_eq!(lesson.title, "Nervous System");
    assert_eq!(lesson.source_path, "materi/biology/anatomy-nervous.md");
    assert!(!lesson.watch_links.0.is_empty());
}

#[renox::test]
async fn the_lesson_page_shows_pictures_and_keeps_the_answer_key_closed() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    let page = test.get(&format!("/lessons/{NERVOUS}")).await;
    page.assert_ok()
        .assert_see("Nervous System")
        .assert_see("src=\"/content/biology/nervous-brain-cns.svg\"")
        .assert_dont_see("../../public")
        .assert_see("Check your understanding")
        .assert_see("I redrew it from memory")
        .assert_see("Answer key")
        .assert_see("/redraw/biology.anatomy.nervous");
    let text = page.text();
    assert!(
        text.contains("<details><summary>"),
        "the key is a <details>"
    );
    assert!(!text.contains("<details open"), "the key stays closed");
    // The interactive questions: five groups of A-E.
    for field in ["q1", "q2", "q3", "q4", "q5"] {
        assert!(text.contains(&format!("name=\"{field}\"")), "{field}");
    }
    test.get("/lessons/biology.anatomy.nothing")
        .await
        .assert_not_found();
}

#[renox::test]
async fn dangerous_html_in_a_lesson_is_not_executed() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let id = topic(&test, NERVOUS).await.id;
    let mut lesson = Lesson::query()
        .where_(Lesson::TOPIC_ID.eq(id))
        .first(test.db())
        .await
        .unwrap()
        .unwrap();
    lesson.markdown = lesson.markdown.replacen(
        "## 💡 Core ideas",
        "<script>alert('x')</script>\n\n<img src=x onerror=alert(1)>\n\n[bad](javascript:alert(2))\n\n## 💡 Core ideas",
        1,
    );
    lesson.save(test.db()).await.unwrap();
    test.acting_as(&student);
    let text = test.get(&format!("/lessons/{NERVOUS}")).await.text();
    assert!(!text.contains("<script>alert"), "script escaped");
    assert!(!text.contains("<img src=x"), "img escaped");
    assert!(
        !text.contains("href=\"javascript"),
        "javascript: link removed"
    );
}

#[renox::test]
async fn the_check_is_saved_with_its_score() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    submit_check(&test, NERVOUS, 2).await;
    let rows = LessonCheck::query().get(test.db()).await.unwrap();
    assert_eq!(rows.len(), 1);
    assert_eq!(rows[0].user_id, student.id);
    assert_eq!(rows[0].topic_id, topic(&test, NERVOUS).await.id);
    assert_eq!(rows[0].score, Some(3));
    assert_eq!(rows[0].answers.0.len(), 5);
    // The page shows the last result and the explanations.
    test.get(&format!("/lessons/{NERVOUS}"))
        .await
        .assert_ok()
        .assert_see("Last try")
        .assert_see("3 of 5 right")
        .assert_see("Not quite");
}

#[renox::test]
async fn ready_follows_the_rules_over_http() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    let url = format!("/lessons/{NERVOUS}");
    test.get(&url).await.assert_see("Not yet");

    // Drawn alone is not enough.
    mark_drawn(&test, NERVOUS, true).await;
    test.get(&url).await.assert_see("In progress");

    // Drawn, but only 3 of 5: still in progress.
    submit_check(&test, NERVOUS, 2).await;
    test.get(&url)
        .await
        .assert_see("Best check: 3")
        .assert_see("In progress")
        .assert_dont_see("✅ READY");

    // 5 of 5 without a drawing is not enough either.
    mark_drawn(&test, NERVOUS, false).await;
    submit_check(&test, NERVOUS, 0).await;
    test.get(&url)
        .await
        .assert_see("Best check: 5")
        .assert_see("In progress")
        .assert_dont_see("✅ READY");

    // Both: READY.
    mark_drawn(&test, NERVOUS, true).await;
    test.get(&url).await.assert_see("✅ READY");
}

#[renox::test]
async fn drawn_and_four_of_five_make_a_subtopic_ready() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    submit_check(&test, NERVOUS, 1).await; // 4 of 5
    mark_drawn(&test, NERVOUS, true).await;
    let page = test.get(&format!("/lessons/{NERVOUS}")).await;
    page.assert_ok()
        .assert_see("✅ READY")
        .assert_see("Drawn from memory");
    test.get("/lessons")
        .await
        .assert_ok()
        .assert_see("✅ READY")
        .assert_see("1 / ")
        .assert_see("Nervous System");
    // Unticking the mark takes it back.
    mark_drawn(&test, NERVOUS, false).await;
    test.get(&format!("/lessons/{NERVOUS}"))
        .await
        .assert_dont_see("✅ READY");
}

#[renox::test]
async fn a_saved_drawing_counts_as_drawn() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    submit_check(&test, NERVOUS, 0).await;
    test.get(&format!("/lessons/{NERVOUS}"))
        .await
        .assert_dont_see("✅ READY");
    renox::db::sql(
        "INSERT INTO drawings (user_id, topic_id, image_path) VALUES (?, ?, 'drawings/x.png')",
    )
    .bind(student.id)
    .bind(topic(&test, NERVOUS).await.id)
    .execute(test.db())
    .await
    .unwrap();
    test.get(&format!("/lessons/{NERVOUS}"))
        .await
        .assert_see("✅ READY");
}

#[renox::test]
async fn once_flashcards_exist_the_cards_must_be_in_box_three() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    let id = topic(&test, NERVOUS).await.id;
    renox::db::sql(
        "INSERT INTO flashcards (key, topic_id, card_type, front, back, payload, tags, origin) \
         VALUES ('lesson-test-1', ?, 'basic', 'Q', 'A', '{}', '[]', 'content')",
    )
    .bind(id)
    .execute(test.db())
    .await
    .unwrap();
    // Every card of the subtopic (the real ones too) is in box 2.
    renox::db::sql(
        "INSERT INTO card_states (user_id, flashcard_id, box, due_on, introduced_on) \
         SELECT ?, id, 2, '2026-10-20', '2026-10-12' FROM flashcards WHERE topic_id = ?",
    )
    .bind(student.id)
    .bind(id)
    .execute(test.db())
    .await
    .unwrap();

    submit_check(&test, NERVOUS, 0).await;
    mark_drawn(&test, NERVOUS, true).await;
    let url = format!("/lessons/{NERVOUS}");
    test.get(&url).await.assert_see("In progress");

    renox::db::sql("UPDATE card_states SET box = 3")
        .execute(test.db())
        .await
        .unwrap();
    test.get(&url).await.assert_see("✅ READY");
}

#[renox::test]
async fn today_links_the_new_material_with_its_status() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 19);
    test.acting_as(&student);
    let page = test.get("/today").await;
    page.assert_ok()
        .assert_see("New material today")
        .assert_see("Nervous System")
        .assert_see(&format!("/lessons/{NERVOUS}"))
        .assert_see("Not yet");
    submit_check(&test, NERVOUS, 0).await;
    mark_drawn(&test, NERVOUS, true).await;
    test.get("/today").await.assert_see("✅ READY");
}

#[renox::test]
async fn sunday_shows_the_red_list_of_late_subtopics() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;

    // Monday 26 Oct: no red list. Sunday 25 Oct: yes.
    travel_to(&test, 10, 26);
    test.acting_as(&student);
    test.get("/today").await.assert_dont_see("not READY yet");
    let sunday = NaiveDate::from_ymd_opt(2026, 10, 25).unwrap();
    // The clock is on the 26th, so the 25th is looked at with ?date=.
    let page = test.get(&format!("/today?date={sunday}")).await;
    page.assert_ok()
        .assert_see("not READY yet")
        .assert_see(&format!("/lessons/{MATH_POLY}"))
        .assert_see("Polynomials")
        // 19 Oct is before the 25th: late as well.
        .assert_see(&format!("/lessons/{NERVOUS}"));
}

#[renox::test]
async fn a_ready_subtopic_leaves_the_red_list() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 10, 25);
    test.acting_as(&student);
    let before = test.get("/today").await;
    before
        .assert_ok()
        .assert_see(&format!("/lessons/{MATH_POLY}"));
    submit_check(&test, MATH_POLY, 0).await;
    mark_drawn(&test, MATH_POLY, true).await;
    let after = test.get("/today").await.text();
    let red = after.split("id=\"red-list\"").nth(1).expect("red list");
    let red = red.split("</ul>").next().unwrap();
    assert!(!red.contains(MATH_POLY), "READY items leave the red list");
    assert!(red.contains("math.algebra.sequences"), "others stay");
}

#[renox::test]
async fn in_the_last_week_the_red_list_follows_the_subject_of_the_day() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 11, 9); // the math day
    test.acting_as(&student);
    let page = test.get("/today").await;
    page.assert_ok()
        .assert_see("Red list: Mathematics")
        .assert_see(&format!("/lessons/{MATH_POLY}"));
    let text = page.text();
    let red = text.split("id=\"red-list\"").nth(1).expect("red list");
    let red = red.split("</ul>").next().unwrap();
    assert!(!red.contains("biology."), "other subjects are not listed");
}

#[renox::test]
async fn the_biology_day_lists_biology() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    travel_to(&test, 11, 11); // the biology day
    test.acting_as(&student);
    test.get("/today")
        .await
        .assert_see("Red list: Biology")
        .assert_see(&format!("/lessons/{NERVOUS}"));
}

#[renox::test]
async fn the_parent_reads_but_cannot_save() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    let parent = user(&test, "parent@huso.local").await;
    test.acting_as(&student);
    submit_check(&test, NERVOUS, 0).await;
    mark_drawn(&test, NERVOUS, true).await;

    test.acting_as(&parent);
    test.get(&format!("/lessons/{NERVOUS}"))
        .await
        .assert_ok()
        .assert_see("✅ READY")
        .assert_see("Best check: 5")
        .assert_dont_see("I redrew it from memory")
        .assert_dont_see("Check my answers");
    test.get("/lessons")
        .await
        .assert_ok()
        .assert_see("✅ READY");
    test.post(&format!("/lessons/{NERVOUS}/drawn"), &[("drawn", "false")])
        .await
        .assert_forbidden();
    test.post(&format!("/lessons/{NERVOUS}/check"), &[("q1", "A")])
        .await
        .assert_forbidden();
    assert_eq!(LessonCheck::query().count(test.db()).await.unwrap(), 1);
}

#[renox::test]
async fn guests_are_sent_to_the_login() {
    let test = seeded().await;
    // Reading is public; saving is not.
    test.get("/lessons").await.assert_ok();
    test.get(&format!("/lessons/{NERVOUS}")).await.assert_ok();
    test.post(&format!("/lessons/{NERVOUS}/check"), &[("q1", "A")])
        .await
        .assert_redirect("/login");
}

#[renox::test]
async fn the_navigation_has_materials() {
    let test = seeded().await;
    let student = user(&test, "student@huso.local").await;
    test.acting_as(&student);
    test.get("/lessons")
        .await
        .assert_ok()
        .assert_see("href=\"/lessons\"")
        .assert_see("Materials")
        .assert_see("Mathematics")
        .assert_see("Nervous System");
}
