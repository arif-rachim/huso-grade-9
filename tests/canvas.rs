use huso::app;
use huso::app::canvas::Drawing;
use huso::app::content::models::{Flashcard, Subject, Topic};
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;

/// A 1x1 PNG.
const PNG: &[u8] = &[
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
    0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA7, 0x35, 0x81, 0x84, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82,
];

const SLUG: &str = "canvas-test.sub";

async fn setup() -> (TestApp, User, User, Topic) {
    let test = TestApp::new(app()).await;
    test.kernel().seed().await.unwrap();
    let db = test.db();
    let subject = Subject::create(
        db,
        Subject {
            slug: "canvas-test".into(),
            name: "Canvas test".into(),
            color: "#16a34a".into(),
            emoji: "G".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let topic = Topic::create(
        db,
        Topic {
            slug: SLUG.into(),
            subject_id: subject.id,
            parent_id: Some(1),
            name: "Heart chambers".into(),
            items: Json(vec!["Left ventricle".into(), "Aorta".into()]),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let student = User::find_by_email(db, "student@huso.local")
        .await
        .unwrap()
        .unwrap();
    let parent = User::find_by_email(db, "parent@huso.local")
        .await
        .unwrap()
        .unwrap();
    (test, student, parent, topic)
}

async fn save(test: &TestApp, notes: &str) -> renox::testing::TestResponse {
    test.post_multipart(
        &format!("/redraw/{SLUG}"),
        &[("notes", notes)],
        &[("image", "drawing.png", PNG)],
    )
    .await
}

#[renox::test]
async fn the_student_saves_a_drawing_and_sees_it_again() {
    let (test, student, _, topic) = setup().await;
    test.acting_as(&student);
    test.get(&format!("/redraw/{SLUG}"))
        .await
        .assert_ok()
        .assert_see("Heart chambers")
        .assert_see("data-redraw-canvas");

    let saved = save(&test, "forgot the valves").await;
    saved.assert_status(303);
    test.assert_database_count("drawings", 1).await;
    let drawing = Drawing::query().first(test.db()).await.unwrap().unwrap();
    assert_eq!(drawing.user_id, student.id);
    assert_eq!(drawing.topic_id, topic.id);
    assert_eq!(drawing.notes.as_deref(), Some("forgot the valves"));
    assert!(
        test.state()
            .storage
            .exists(&drawing.image_path)
            .await
            .unwrap()
    );

    test.get(&format!("/redraw/drawings/{}", drawing.id))
        .await
        .assert_ok()
        .assert_see("Left ventricle")
        .assert_see("forgot the valves")
        .assert_see("No reference picture");
    let image = test
        .get(&format!("/redraw/drawings/{}/image", drawing.id))
        .await;
    image.assert_ok().assert_header("content-type", "image/png");
    assert_eq!(image.body.as_ref(), PNG);
    test.get("/redraw")
        .await
        .assert_ok()
        .assert_see("Heart chambers")
        .assert_see(&format!("/redraw/drawings/{}/image", drawing.id));
}

#[renox::test]
async fn the_reference_is_the_flashcard_picture_of_the_subtopic() {
    let (test, student, _, topic) = setup().await;
    Flashcard::create(
        test.db(),
        Flashcard {
            key: "canvas-test-0001".into(),
            topic_id: topic.id,
            card_type: "basic".into(),
            front: "Q".into(),
            back: "A".into(),
            visual: Some("content/biology/heart-chambers.svg".into()),
            origin: "content".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    test.acting_as(&student);
    save(&test, "").await;
    let drawing = Drawing::query().first(test.db()).await.unwrap().unwrap();
    test.get(&format!("/redraw/drawings/{}", drawing.id))
        .await
        .assert_ok()
        .assert_see("/content/biology/heart-chambers.svg")
        .assert_dont_see("No reference picture");
}

#[renox::test]
async fn only_images_are_accepted() {
    let (test, student, _, _) = setup().await;
    test.acting_as(&student);
    let _ = test
        .post_multipart(
            &format!("/redraw/{SLUG}"),
            &[],
            &[("image", "x.png", b"not an image")],
        )
        .await;
    test.assert_database_count("drawings", 0).await;
    test.post_multipart(&format!("/redraw/{SLUG}"), &[], &[])
        .await;
    test.assert_database_count("drawings", 0).await;
}

#[renox::test]
async fn an_unknown_subtopic_is_a_404() {
    let (test, student, _, _) = setup().await;
    test.acting_as(&student);
    test.get("/redraw/nope.nothing").await.assert_not_found();
}

#[renox::test]
async fn the_parent_reads_the_gallery_but_cannot_draw() {
    let (test, student, parent, _) = setup().await;
    test.acting_as(&student);
    save(&test, "mine").await;
    let drawing = Drawing::query().first(test.db()).await.unwrap().unwrap();

    test.acting_as(&parent);
    test.get("/redraw")
        .await
        .assert_ok()
        .assert_see("Heart chambers")
        .assert_see("read-only")
        .assert_dont_see("Pick a subtopic");
    test.get(&format!("/redraw/drawings/{}", drawing.id))
        .await
        .assert_ok()
        .assert_see("mine")
        .assert_dont_see("Redraw again");
    test.get(&format!("/redraw/drawings/{}/image", drawing.id))
        .await
        .assert_ok();
    test.get(&format!("/redraw/{SLUG}"))
        .await
        .assert_forbidden();
    save(&test, "sneaky").await.assert_forbidden();
    test.assert_database_count("drawings", 1).await;
}

#[renox::test]
async fn guests_are_sent_to_login() {
    let (test, _, _, _) = setup().await;
    test.get("/redraw").await.assert_redirect("/login");
    test.get(&format!("/redraw/{SLUG}"))
        .await
        .assert_redirect("/login");
}

#[renox::test]
async fn the_canvas_script_is_served() {
    let (test, student, _, _) = setup().await;
    test.acting_as(&student);
    test.get("/redraw/drawings/999").await.assert_not_found();
    test.get("/js/canvas.js").await.assert_ok();
}
