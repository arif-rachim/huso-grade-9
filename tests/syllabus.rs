use huso::app;
use huso::app::content::models::{Flashcard, Question, Subject, Topic};
use huso::app::errors::models::ErrorEntry;
use huso::app::flashcards::deck;
use huso::app::flashcards::models::CardState;
use huso::app::practice::models::{Answer, Attempt};
use huso::app::syllabus::{mastery_by_subtopic, mastery_by_topic_id};
use huso::clock;
use renox::chrono::Duration;
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;
use std::sync::atomic::{AtomicUsize, Ordering};

static NEXT: AtomicUsize = AtomicUsize::new(1000);

struct World {
    app: TestApp,
    student: User,
    parent: User,
    /// The subtopics of "Physics", in order (`physics.t0`, `physics.t1`, ...).
    subs: Vec<Topic>,
}

async fn world(subtopics: usize) -> World {
    let app = TestApp::new(app()).await;
    huso::app::accounts::seed(app.db(), &app.state().config)
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
    let subject = Subject::create(
        app.db(),
        Subject {
            slug: "physics".into(),
            name: "Physics".into(),
            color: "#dc2626".into(),
            emoji: "*".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let topic = Topic::create(
        app.db(),
        Topic {
            slug: "physics.mechanics".into(),
            subject_id: subject.id,
            name: "Mechanics".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let mut subs = Vec::new();
    for i in 0..subtopics {
        subs.push(
            Topic::create(
                app.db(),
                Topic {
                    slug: format!("physics.t{i}"),
                    subject_id: subject.id,
                    parent_id: Some(topic.id),
                    name: format!("Sub {i}"),
                    items: Json(vec![format!("Point {i}a"), format!("Point {i}b")]),
                    position: i as i64,
                    ..Default::default()
                },
            )
            .await
            .unwrap(),
        );
    }
    World {
        app,
        student,
        parent,
        subs,
    }
}

async fn question(w: &World, topic: &Topic, n: usize) -> Question {
    Question::create(
        w.app.db(),
        Question {
            key: format!("{}-q{n}", topic.slug),
            topic_id: topic.id,
            difficulty: 1,
            stem: format!("Stem {n}"),
            choice_a: "a".into(),
            choice_b: "b".into(),
            choice_c: "c".into(),
            choice_d: "d".into(),
            choice_e: "e".into(),
            answer: "A".into(),
            explanation: "because".into(),
            source: "original".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap()
}

/// Gives `kinds` answers: 'c' correct, 'g' correct but guessed, 'w' wrong, 'b' blank.
/// `days_ago` moves them back in time.
async fn answer_all(w: &World, topic: &Topic, kinds: &str, days_ago: i64) {
    let when = renox::db::now() - Duration::days(days_ago);
    let attempt = Attempt::create(
        w.app.db(),
        Attempt {
            user_id: w.student.id,
            mode: "topic".into(),
            started_at: when,
            ..Default::default()
        },
    )
    .await
    .unwrap();
    for (i, kind) in kinds.chars().enumerate() {
        let q = question(w, topic, NEXT.fetch_add(1, Ordering::Relaxed)).await;
        Answer::create(
            w.app.db(),
            Answer {
                attempt_id: attempt.id,
                question_id: q.id,
                position: i as i64,
                choice: (kind != 'b').then(|| "A".to_owned()),
                is_correct: matches!(kind, 'c' | 'g'),
                guessed: kind == 'g',
                answered_at: Some(when),
                ..Default::default()
            },
        )
        .await
        .unwrap();
    }
}

/// `boxes` cards for the topic: one per entry, with a state in that box (0 = never reviewed).
async fn cards(w: &World, topic: &Topic, boxes: &[i64]) -> Vec<Flashcard> {
    let mut out = Vec::new();
    for (i, b) in boxes.iter().enumerate() {
        let card = Flashcard::create(
            w.app.db(),
            Flashcard {
                key: format!("{}-c{i}", topic.slug),
                topic_id: topic.id,
                card_type: "basic".into(),
                front: format!("Front {}-{i}", topic.slug),
                back: "Back".into(),
                sketch_prompt: Some("Draw".into()),
                payload: Json(json!({})),
                tags: Json(vec![]),
                origin: "content".into(),
                ..Default::default()
            },
        )
        .await
        .unwrap();
        if *b > 0 {
            CardState::create(
                w.app.db(),
                CardState {
                    user_id: w.student.id,
                    flashcard_id: card.id,
                    r#box: *b,
                    due_on: clock::today() + Duration::days(3),
                    reviews: 1,
                    introduced_on: clock::today(),
                    ..Default::default()
                },
            )
            .await
            .unwrap();
        }
        out.push(card);
    }
    out
}

#[renox::test]
async fn ten_answers_and_four_cards_give_the_formula_value() {
    let w = world(3).await;
    // 8 correct, 1 correct-but-guessed, 1 wrong; 4 cards, 2 of them in box 3 or higher.
    answer_all(&w, &w.subs[0], "cccccccc", 0).await;
    answer_all(&w, &w.subs[0], "gw", 0).await;
    cards(&w, &w.subs[0], &[3, 5, 1, 0]).await;
    let map = mastery_by_subtopic(w.app.db(), w.student.id).await.unwrap();
    assert_eq!(map.len(), 3);
    assert_eq!(map["physics.t0"], Some(71));
    assert_eq!(
        map["physics.t1"], None,
        "untouched subtopics are not started"
    );
    let by_id = mastery_by_topic_id(w.app.db(), w.student.id).await.unwrap();
    assert_eq!(by_id.get(&w.subs[0].id), Some(&71));
    assert!(!by_id.contains_key(&w.subs[1].id));
}

#[renox::test]
async fn only_the_last_14_days_and_only_real_answers_count() {
    let w = world(1).await;
    answer_all(&w, &w.subs[0], "ccccc", 20).await;
    let map = mastery_by_subtopic(w.app.db(), w.student.id).await.unwrap();
    assert_eq!(map["physics.t0"], None, "old answers do not count");
    answer_all(&w, &w.subs[0], "ccb", 1).await;
    let map = mastery_by_subtopic(w.app.db(), w.student.id).await.unwrap();
    assert_eq!(map["physics.t0"], None, "a blank is not an answer: 2 < 3");
    answer_all(&w, &w.subs[0], "w", 2).await;
    let map = mastery_by_subtopic(w.app.db(), w.student.id).await.unwrap();
    assert_eq!(map["physics.t0"], Some(67), "2 of 3 right, no cards");
}

#[renox::test]
async fn the_map_has_the_same_number_of_queries_for_any_number_of_subtopics() {
    async fn count(subtopics: usize) -> usize {
        let w = world(subtopics).await;
        for sub in &w.subs {
            answer_all(&w, sub, "ccw", 0).await;
            cards(&w, sub, &[1, 4]).await;
        }
        w.app.acting_as(&w.student);
        let (res, queries) = renox::db::capture_queries(w.app.get("/syllabus")).await;
        res.assert_ok();
        queries.len()
    }
    let few = count(2).await;
    let many = count(25).await;
    assert_eq!(few, many, "{few} queries for 2 subtopics, {many} for 25");
}

#[renox::test]
async fn the_index_colours_tiles_and_filters_red_and_grey() {
    let w = world(3).await;
    answer_all(&w, &w.subs[0], "cccc", 0).await; // 100 -> green
    answer_all(&w, &w.subs[1], "wwwc", 0).await; // 25 -> red
    w.app.acting_as(&w.student);
    let page = w.app.get("/syllabus").await;
    page.assert_ok()
        .assert_see("Syllabus map")
        .assert_see("Sub 0")
        .assert_see("100%")
        .assert_see("25%")
        .assert_see(r#"data-band="green""#)
        .assert_see(r#"data-band="red""#)
        .assert_see(r#"data-band="grey""#)
        .assert_see("Show only red &amp; grey")
        .assert_see("#dc2626");
    let weak = w.app.get("/syllabus?only=weak").await;
    weak.assert_ok()
        .assert_dont_see("Sub 0")
        .assert_see("Sub 1")
        .assert_see("Sub 2");
}

#[renox::test]
async fn a_subtopic_page_shows_the_breakdown_and_the_buttons() {
    let w = world(2).await;
    let sub = w.subs[0].clone();
    answer_all(&w, &sub, "ccw", 0).await;
    cards(&w, &sub, &[1, 3, 0]).await;
    ErrorEntry::create(
        w.app.db(),
        ErrorEntry {
            user_id: w.student.id,
            origin: "manual".into(),
            topic_id: sub.id,
            subject: "physics".into(),
            cause: Some("concept".into()),
            box_no: 1,
            due_on: clock::today(),
            status: "open".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();

    w.app.acting_as(&w.student);
    w.app
        .get("/syllabus/physics.t0")
        .await
        .assert_ok()
        .assert_see("Point 0a")
        .assert_see("53%")
        .assert_see("67%</strong> right")
        .assert_see("1 of 3")
        .assert_see("Box 1: 1")
        .assert_see("Not started: 1")
        .assert_see("Concept")
        .assert_see("Practise 10 questions on this subtopic")
        .assert_see("cards")
        .assert_see("/flashcards/review?subtopic=physics.t0")
        .assert_see("/redraw/physics.t0");
    w.app.get("/syllabus/physics.nope").await.assert_status(404);

    // The parent reads the student's numbers but gets no buttons.
    w.app.acting_as(&w.parent);
    w.app
        .get("/syllabus/physics.t0")
        .await
        .assert_ok()
        .assert_see("67%")
        .assert_dont_see("Practise 10 questions")
        .assert_dont_see("/redraw/physics.t0");
    w.app.get("/syllabus").await.assert_ok().assert_see("53%");
}

#[renox::test]
async fn the_practice_button_opens_topic_mode_on_that_subtopic() {
    let w = world(2).await;
    for n in 0..12 {
        question(&w, &w.subs[1], n).await;
        question(&w, &w.subs[0], 100 + n).await;
    }
    w.app.acting_as(&w.student);
    w.app
        .post(
            "/practice",
            &[("mode", "topic"), ("topic_slug", "physics.t1")],
        )
        .await
        .assert_status(303);
    let attempt = Attempt::query()
        .order_by_desc(Attempt::ID)
        .first(w.app.db())
        .await
        .unwrap()
        .unwrap();
    assert_eq!(attempt.mode, "topic");
    assert_eq!(attempt.topic_id, Some(w.subs[1].id));
    assert_eq!(attempt.question_ids.0.len(), 10);
    let questions = Question::query()
        .where_(Question::ID.is_in(attempt.question_ids.0.clone()))
        .get(w.app.db())
        .await
        .unwrap();
    assert!(questions.iter().all(|q| q.topic_id == w.subs[1].id));
}

#[renox::test]
async fn the_review_button_opens_only_that_subtopics_cards() {
    let w = world(2).await;
    cards(&w, &w.subs[0], &[0, 0]).await;
    cards(&w, &w.subs[1], &[0, 0, 0]).await;
    let all = deck::queue_for(w.app.db(), w.student.id, clock::today(), None)
        .await
        .unwrap();
    assert_eq!(all.items.len(), 5);
    let one = deck::queue_for(w.app.db(), w.student.id, clock::today(), Some("physics.t1"))
        .await
        .unwrap();
    assert_eq!(one.items.len(), 3);
    // The route takes the same filter; a made-up slug means "everything".
    w.app.acting_as(&w.student);
    w.app
        .get("/flashcards/review?subtopic=physics.t1")
        .await
        .assert_ok()
        .assert_see("Front physics.t1-0")
        .assert_dont_see("Front physics.t0-0");
    w.app
        .get("/flashcards/review?subtopic=nonsense")
        .await
        .assert_ok();
}

#[renox::test]
async fn the_models_match_the_schema_and_the_views_compile() {
    let w = world(1).await;
    w.app.acting_as(&w.student);
    w.app.get("/syllabus").await.assert_ok();
}
