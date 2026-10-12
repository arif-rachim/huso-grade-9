use huso::app;
use huso::app::content::models::{Question, Subject, Topic};
use huso::app::errors::models::ErrorEntry;
use huso::app::errors::{record, stats};
use huso::app::practice::engine;
use huso::app::practice::models::{Answer, Attempt};
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;
use std::time::Duration;

/// A 1x1 PNG.
const PNG: &[u8] = &[
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
    0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA7, 0x35, 0x81, 0x84, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82,
];

const DAY: Duration = Duration::from_secs(24 * 60 * 60);

struct Fixture {
    app: TestApp,
    student: User,
    parent: User,
    /// Subtopics: physics (red), biology (green).
    physics: Topic,
    biology: Topic,
    questions: Vec<Question>,
}

async fn subtopic(app: &TestApp, slug: &str, name: &str, color: &str, position: i64) -> Topic {
    let subject = Subject::create(
        app.db(),
        Subject {
            slug: slug.into(),
            name: name.into(),
            color: color.into(),
            emoji: "*".into(),
            position,
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let topic = Topic::create(
        app.db(),
        Topic {
            slug: slug.into(),
            subject_id: subject.id,
            name: format!("{name} topic"),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    Topic::create(
        app.db(),
        Topic {
            slug: format!("{slug}.sub"),
            subject_id: subject.id,
            parent_id: Some(topic.id),
            name: format!("{name} subtopic"),
            items: Json(vec![]),
            ..Default::default()
        },
    )
    .await
    .unwrap()
}

/// Five questions: 1-3 in physics, 4-5 in biology. The key of every question is "A".
async fn fixture() -> Fixture {
    let app = TestApp::new(app()).await;
    app::accounts::seed(app.db(), &app.state().config)
        .await
        .unwrap();
    let student = User::find_by_email(app.db(), "student@huso.local")
        .await
        .unwrap()
        .unwrap();
    let parent = User::find_by_email(app.db(), "parent@huso.local")
        .await
        .unwrap()
        .unwrap();
    let physics = subtopic(&app, "physics", "Physics", "#dc2626", 1).await;
    let biology = subtopic(&app, "biology", "Biology", "#16a34a", 2).await;
    let mut questions = Vec::new();
    for n in 1..=5 {
        let topic = if n <= 3 { &physics } else { &biology };
        questions.push(
            Question::create(
                app.db(),
                Question {
                    key: format!("q-{n:04}"),
                    topic_id: topic.id,
                    difficulty: 1,
                    stem: format!("Stem-{n}"),
                    choice_a: "first".into(),
                    choice_b: "second".into(),
                    choice_c: "third".into(),
                    choice_d: "fourth".into(),
                    choice_e: "fifth".into(),
                    answer: "A".into(),
                    explanation: format!("Why-{n}"),
                    source: "original".into(),
                    ..Default::default()
                },
            )
            .await
            .unwrap(),
        );
    }
    Fixture {
        app,
        student,
        parent,
        physics,
        biology,
        questions,
    }
}

/// What the student did with one question: `(choice, guessed)`; `None` = blank.
type Given = Option<(&'static str, bool)>;

/// A finished attempt over `questions[i]` with the given answers (key "A").
async fn finished_attempt(f: &Fixture, picks: &[(usize, Given)]) -> Attempt {
    let now = renox::db::now();
    let attempt = Attempt::create(
        f.app.db(),
        Attempt {
            user_id: f.student.id,
            mode: "mixed".into(),
            started_at: now,
            question_ids: Json(picks.iter().map(|(i, _)| f.questions[*i].id).collect()),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    for (position, (i, given)) in picks.iter().enumerate() {
        Answer::create(
            f.app.db(),
            Answer {
                attempt_id: attempt.id,
                question_id: f.questions[*i].id,
                position: position as i64,
                choice: given.map(|(c, _)| c.to_owned()),
                is_correct: given.is_some_and(|(c, _)| c == "A"),
                guessed: given.is_some_and(|(_, g)| g),
                answered_at: given.map(|_| now),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    }
    engine::finish_attempt(f.app.db(), attempt.id)
        .await
        .unwrap()
}

async fn entries(f: &Fixture) -> Vec<ErrorEntry> {
    ErrorEntry::query()
        .order_by(ErrorEntry::ID)
        .get(f.app.db())
        .await
        .unwrap()
}

async fn entry_for(f: &Fixture, question: usize) -> ErrorEntry {
    ErrorEntry::query()
        .where_(ErrorEntry::QUESTION_ID.eq(f.questions[question].id))
        .order_by_desc(ErrorEntry::ID)
        .first(f.app.db())
        .await
        .unwrap()
        .expect("an entry")
}

#[renox::test]
async fn a_finished_attempt_logs_wrong_and_guessed_answers_but_not_blanks() {
    let f = fixture().await;
    finished_attempt(
        &f,
        &[
            (0, Some(("B", false))), // wrong
            (1, Some(("C", false))), // wrong
            (2, Some(("A", true))),  // correct but guessed
            (3, None),               // blank
            (4, Some(("A", false))), // correct
        ],
    )
    .await;
    let all = entries(&f).await;
    assert_eq!(
        all.len(),
        3,
        "2 wrong + 1 guessed, no blank, no clean right"
    );
    assert!(all.iter().all(|e| e.box_no == 1 && e.status == "open"));
    assert!(all.iter().all(|e| e.user_id == f.student.id));
    let today = huso::clock::today();
    assert!(
        all.iter()
            .all(|e| e.due_on == today + renox::chrono::Duration::days(1)),
        "due tomorrow"
    );
    assert_eq!(entry_for(&f, 0).await.cause, None, "wrong: no cause yet");
    assert_eq!(entry_for(&f, 2).await.cause.as_deref(), Some("guess"));
    assert_eq!(entry_for(&f, 0).await.subject, "physics");
    assert_eq!(entry_for(&f, 0).await.topic_id, f.physics.id);
}

#[renox::test]
async fn logging_twice_or_repeating_a_question_does_not_duplicate() {
    let f = fixture().await;
    let attempt = finished_attempt(&f, &[(0, Some(("B", false))), (3, Some(("C", false)))]).await;
    assert_eq!(entries(&f).await.len(), 2);

    // The same attempt again (engine finish is idempotent, and so is the log).
    engine::finish_attempt(f.app.db(), attempt.id)
        .await
        .unwrap();
    assert_eq!(
        record::record_attempt(f.app.db(), attempt.id)
            .await
            .unwrap(),
        0
    );
    assert_eq!(entries(&f).await.len(), 2);

    // Move the first entry up the boxes, then get the same question wrong in a new attempt.
    let mut e = entry_for(&f, 0).await;
    e.box_no = 4;
    e.due_on = huso::clock::today() + renox::chrono::Duration::days(30);
    e.save(f.app.db()).await.unwrap();
    finished_attempt(&f, &[(0, Some(("D", false)))]).await;
    let all = entries(&f).await;
    assert_eq!(all.len(), 2, "still one entry per question");
    let e = entry_for(&f, 0).await;
    assert_eq!(e.box_no, 1, "reset to box 1");
    assert_eq!(
        e.due_on,
        huso::clock::today() + renox::chrono::Duration::days(1)
    );
}

#[renox::test]
async fn a_resolved_question_gets_a_new_entry_when_missed_again() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false)))]).await;
    let mut e = entry_for(&f, 0).await;
    e.status = "resolved".into();
    e.resolved_at = Some(renox::db::now());
    e.save(f.app.db()).await.unwrap();
    finished_attempt(&f, &[(0, Some(("B", false)))]).await;
    assert_eq!(entries(&f).await.len(), 2);
}

#[renox::test]
async fn a_manual_entry_with_a_photo_is_saved_and_shown() {
    let f = fixture().await;
    f.app.acting_as(&f.student);
    f.app
        .get("/errors/new")
        .await
        .assert_ok()
        .assert_see("Add a mistake");

    // A note or a photo is required.
    f.app
        .htmx()
        .post(
            "/errors",
            &[
                ("topic", &f.physics.id.to_string()),
                ("cause", "misread"),
                ("note", ""),
            ],
        )
        .await
        .assert_invalid("note");
    assert!(entries(&f).await.is_empty());

    let topic = f.physics.id.to_string();
    let saved = f
        .app
        .post_multipart(
            "/errors",
            &[
                ("topic", topic.as_str()),
                ("cause", "misread"),
                ("source", "HUSO 2024 Round 1 (Grade 9–10)"),
                ("question_no", "17"),
                ("note", "Read the units."),
            ],
            &[("photo", "sketch.png", PNG)],
        )
        .await;
    saved.assert_status(303);
    let all = entries(&f).await;
    assert_eq!(all.len(), 1);
    let e = &all[0];
    assert_eq!(e.origin, "manual");
    assert_eq!(e.cause.as_deref(), Some("misread"));
    assert_eq!(e.subject, "physics");
    assert_eq!(e.question_no.as_deref(), Some("17"));
    assert!(
        f.app
            .state()
            .storage
            .exists(e.photo.as_ref().unwrap())
            .await
            .unwrap()
    );

    f.app
        .get("/errors")
        .await
        .assert_ok()
        .assert_see(&format!("/errors/{}/image", e.id))
        .assert_see("Physics subtopic");
    let image = f.app.get(&format!("/errors/{}/image", e.id)).await;
    image.assert_ok().assert_header("content-type", "image/png");
    assert_eq!(image.body.as_ref(), PNG);
    f.app
        .get(&format!("/errors/{}", e.id))
        .await
        .assert_ok()
        .assert_see("Read the units.");
}

#[renox::test]
async fn photo_only_manual_entry_and_photo_replacement() {
    let f = fixture().await;
    f.app.acting_as(&f.student);
    let topic = f.biology.id.to_string();
    f.app
        .post_multipart(
            "/errors",
            &[("topic", topic.as_str()), ("cause", "concept")],
            &[("photo", "a.png", PNG)],
        )
        .await
        .assert_status(303);
    let e = entries(&f).await.remove(0);
    let first = e.photo.clone().unwrap();
    f.app
        .post_multipart(
            &format!("/errors/{}/photo", e.id),
            &[],
            &[("photo", "b.png", PNG)],
        )
        .await
        .assert_status(303);
    let after = ErrorEntry::find(f.app.db(), e.id).await.unwrap().unwrap();
    assert_ne!(after.photo.unwrap(), first);
}

#[renox::test]
async fn review_moves_the_boxes_and_resolves_after_box_five() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false)))]).await;
    let id = entry_for(&f, 0).await.id;

    // Due tomorrow: nothing to review today.
    f.app.acting_as(&f.student);
    f.app
        .get("/errors/review")
        .await
        .assert_ok()
        .assert_see("Nothing is due");

    f.app.travel(DAY * 2);
    f.app.acting_as(&f.student);
    // The cause is asked first.
    f.app
        .get("/errors/review")
        .await
        .assert_ok()
        .assert_see("why did this go wrong");
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "good")])
        .await
        .assert_status(422);
    f.app
        .post(
            "/errors/review/cause",
            &[("id", &id.to_string()), ("cause", "rushed")],
        )
        .await
        .assert_status(303);
    f.app
        .get("/errors/review")
        .await
        .assert_ok()
        .assert_see("Stem-1")
        .assert_see("Cause: Rushed");
    // Picking a choice reveals the explanation.
    f.app
        .get("/errors/review?pick=B")
        .await
        .assert_ok()
        .assert_see("Why-1")
        .assert_see("Not this time");

    let today = f
        .app
        .at_travelled_time(async { huso::clock::today() })
        .await;
    let load = || async { ErrorEntry::find(f.app.db(), id).await.unwrap().unwrap() };
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "good")])
        .await
        .assert_status(303);
    let e = load().await;
    assert_eq!((e.box_no, e.reviews), (2, 1));
    assert_eq!(e.due_on, today + renox::chrono::Duration::days(2));
    assert_eq!(e.last_grade.as_deref(), Some("good"));

    // Easy jumps two boxes; Hard stays; Again goes back to 1.
    let mut e = load().await;
    e.due_on = today;
    e.save(f.app.db()).await.unwrap();
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "easy")])
        .await
        .assert_status(303);
    assert_eq!(load().await.box_no, 4);
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "hard")])
        .await;
    assert_eq!(load().await.box_no, 4);
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "again")])
        .await;
    assert_eq!(load().await.box_no, 1);

    // Box 5, then Good: resolved.
    let mut e = load().await;
    e.box_no = 5;
    e.save(f.app.db()).await.unwrap();
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "good")])
        .await
        .assert_status(303);
    let e = load().await;
    assert_eq!(e.status, "resolved");
    assert!(e.resolved_at.is_some());
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "good")])
        .await
        .assert_status(422);
}

#[renox::test]
async fn resolve_and_change_the_cause_from_the_list() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false))), (3, Some(("C", false)))]).await;
    let a = entry_for(&f, 0).await.id;
    let b = entry_for(&f, 3).await.id;
    f.app.acting_as(&f.student);
    f.app
        .put(&format!("/errors/{a}/cause"), &[("cause", "calculation")])
        .await
        .assert_ok();
    assert_eq!(
        ErrorEntry::find(f.app.db(), a)
            .await
            .unwrap()
            .unwrap()
            .cause
            .as_deref(),
        Some("calculation")
    );
    f.app
        .put(&format!("/errors/{a}/cause"), &[("cause", "bogus")])
        .await
        .assert_status(422);
    f.app
        .post(&format!("/errors/{b}/resolve"), &[])
        .await
        .assert_ok();
    let resolved = ErrorEntry::find(f.app.db(), b).await.unwrap().unwrap();
    assert_eq!(resolved.status, "resolved");
    assert!(resolved.resolved_at.is_some());
    f.app
        .get("/errors?in.status=resolved")
        .await
        .assert_ok()
        .assert_see(&format!("/errors/{b}"))
        .assert_dont_see(&format!("/errors/{a}\""));
}

#[renox::test]
async fn the_pie_and_the_top_ten_are_computed_from_the_entries() {
    let f = fixture().await;
    // 3 physics (concept, concept, no cause), 2 biology (guess, concept), one entry of someone else.
    finished_attempt(
        &f,
        &[
            (0, Some(("B", false))),
            (1, Some(("B", false))),
            (2, Some(("B", false))),
            (3, Some(("A", true))),
            (4, Some(("B", false))),
        ],
    )
    .await;
    for (q, cause) in [(0, "concept"), (1, "concept"), (4, "concept")] {
        let mut e = entry_for(&f, q).await;
        e.cause = Some(cause.into());
        e.save(f.app.db()).await.unwrap();
    }
    ErrorEntry::create(
        f.app.db(),
        ErrorEntry {
            user_id: f.parent.id,
            topic_id: f.biology.id,
            subject: "biology".into(),
            due_on: huso::clock::today(),
            status: "open".into(),
            box_no: 1,
            ..Default::default()
        },
    )
    .await
    .unwrap();

    let causes = stats::cause_counts(f.app.db(), f.student.id).await.unwrap();
    assert_eq!(
        causes,
        vec![
            ("concept".to_owned(), 3),
            ("guess".to_owned(), 1),
            ("none".to_owned(), 1)
        ]
    );
    let top = stats::top_subtopics(f.app.db(), f.student.id, 10)
        .await
        .unwrap();
    assert_eq!(top.len(), 2);
    assert_eq!(
        (top[0].name.as_str(), top[0].count, top[0].color.as_str()),
        ("Physics subtopic", 3, "#dc2626")
    );
    assert_eq!(
        (top[1].name.as_str(), top[1].count),
        ("Biology subtopic", 2)
    );
    let limited = stats::top_subtopics(f.app.db(), f.student.id, 1)
        .await
        .unwrap();
    assert_eq!(limited.len(), 1);

    f.app.acting_as(&f.student);
    f.app
        .get("/errors")
        .await
        .assert_ok()
        .assert_see("My top 10 mistakes")
        .assert_see("Why do I get it wrong?")
        .assert_see("Physics subtopic");
}

#[renox::test]
async fn the_parent_reads_but_cannot_change() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false)))]).await;
    let id = entry_for(&f, 0).await.id;
    f.app.acting_as(&f.parent);
    f.app
        .get("/errors")
        .await
        .assert_ok()
        .assert_see("Read-only")
        .assert_see("Physics subtopic")
        .assert_dont_see("Add mistake");
    f.app
        .get(&format!("/errors/{id}"))
        .await
        .assert_ok()
        .assert_see("Stem-1");
    f.app.get("/errors/new").await.assert_forbidden();
    f.app.get("/errors/review").await.assert_forbidden();
    f.app
        .put(&format!("/errors/{id}/cause"), &[("cause", "concept")])
        .await
        .assert_forbidden();
    f.app
        .post(&format!("/errors/{id}/resolve"), &[])
        .await
        .assert_forbidden();
    f.app
        .post(&format!("/errors/{id}/rate"), &[("grade", "good")])
        .await
        .assert_forbidden();
}

#[renox::test]
async fn today_counts_the_due_entries() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false))), (1, Some(("B", false)))]).await;
    let db = f.app.db();
    assert_eq!(
        huso::app::today::summary::errors_due(db, f.student.id)
            .await
            .unwrap(),
        0,
        "due tomorrow"
    );
    f.app.travel(DAY * 2);
    let due = f
        .app
        .at_travelled_time(huso::app::today::summary::errors_due(db, f.student.id))
        .await
        .unwrap();
    assert_eq!(due, 2);
}

#[renox::test]
async fn redo_wrong_questions_asks_the_due_questions_again() {
    let f = fixture().await;
    finished_attempt(&f, &[(0, Some(("B", false))), (3, Some(("C", false)))]).await;
    f.app.acting_as(&f.student);
    f.app
        .post("/practice", &[("mode", "errors")])
        .await
        .assert_status(303); // nothing due yet: back to the practice page with a notice
    assert_eq!(
        Attempt::query()
            .where_(Attempt::MODE.eq("errors"))
            .count(f.app.db())
            .await
            .unwrap(),
        0
    );

    f.app.travel(DAY * 2);
    f.app.acting_as(&f.student);
    f.app
        .get("/errors")
        .await
        .assert_ok()
        .assert_see("Redo wrong questions (2)");
    f.app
        .post("/practice", &[("mode", "errors")])
        .await
        .assert_status(303);
    let attempt = Attempt::query()
        .where_(Attempt::MODE.eq("errors"))
        .first(f.app.db())
        .await
        .unwrap()
        .expect("an errors attempt");
    assert_eq!(attempt.question_ids.0.len(), 2);
    f.app
        .get(&format!("/practice/{}", attempt.id))
        .await
        .assert_ok()
        .assert_see("Redo wrong questions");
}
