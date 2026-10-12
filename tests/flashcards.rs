use huso::app;
use huso::app::content::models::{Flashcard, PlanDay, Subject, Topic};
use huso::app::flashcards::deck::{self, Deck};
use huso::app::flashcards::models::{CardReview, CardState};
use huso::app::flashcards::review::{self, Review};
use huso::clock;
use renox::chrono::{Duration as Days, NaiveDate};
use renox::db::Json;
use renox::prelude::*;
use renox::testing::TestApp;
use std::path::PathBuf;
use std::time::Duration;

/// A tiny but real PNG (1x1), for uploads.
const PNG: &[u8] = &[
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x08, 0x06, 0x00, 0x00, 0x00, 0x1f, 0x15, 0xc4,
    0x89, 0x00, 0x00, 0x00, 0x0d, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9c, 0x63, 0xf8, 0xff, 0xff, 0x3f,
    0x00, 0x05, 0xfe, 0x02, 0xfe, 0xa7, 0x35, 0x81, 0x84, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e,
    0x44, 0xae, 0x42, 0x60, 0x82,
];

struct Ctx {
    app: TestApp,
    student: User,
    parent: User,
}

/// A seeded app with the real syllabus but no flashcards and no plan days (each test adds
/// the cards it needs, so the content files never change the numbers).
async fn setup() -> Ctx {
    deck::use_public_dir(PathBuf::from("tests/fixtures/public"));
    let app = TestApp::new(app()).await;
    app.kernel().seed().await.unwrap();
    let db = app.db();
    Flashcard::query().delete(db).await.unwrap();
    PlanDay::query().delete(db).await.unwrap();
    let student = User::find_by_email(db, "student@huso.local")
        .await
        .unwrap()
        .unwrap();
    let parent = User::find_by_email(db, "parent@huso.local")
        .await
        .unwrap()
        .unwrap();
    Ctx {
        app,
        student,
        parent,
    }
}

async fn subtopic(db: &Db, subject: &str) -> Topic {
    let s = Subject::query()
        .where_(Subject::SLUG.eq(subject))
        .first(db)
        .await
        .unwrap()
        .unwrap();
    Topic::query()
        .where_(Topic::SUBJECT_ID.eq(s.id))
        .where_(Topic::PARENT_ID.is_not_null())
        .order_by(Topic::POSITION)
        .first(db)
        .await
        .unwrap()
        .unwrap()
}

async fn card(db: &Db, subject: &str, kind: &str, front: &str) -> Flashcard {
    let topic = subtopic(db, subject).await;
    let n = Flashcard::query().count(db).await.unwrap();
    Flashcard::create(
        db,
        Flashcard {
            key: format!("{subject}-{n:04}"),
            topic_id: topic.id,
            card_type: kind.to_owned(),
            front: front.to_owned(),
            back: format!("Answer to {front}"),
            sketch_prompt: Some("Draw it".to_owned()),
            payload: Json(json!({})),
            tags: Json(vec![]),
            origin: "content".to_owned(),
            ..Default::default()
        },
    )
    .await
    .unwrap()
}

async fn cards(db: &Db, subject: &str, n: usize) -> Vec<Flashcard> {
    let mut out = Vec::new();
    for i in 0..n {
        out.push(card(db, subject, "basic", &format!("{subject} question {i}")).await);
    }
    out
}

async fn plan_for_today(db: &Db, subject: &str) {
    PlanDay::create(
        db,
        PlanDay {
            date: clock::today(),
            phase: "intensive".into(),
            minutes: 60,
            subject: subject.into(),
            title: "Test day".into(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
}

/// `due_count` for the student on the (possibly travelled) clock.
async fn due_now(ctx: &Ctx) -> i64 {
    ctx.app
        .at_travelled_time(async {
            deck::due_count(ctx.app.db(), ctx.student.id, clock::today())
                .await
                .unwrap()
        })
        .await
}

async fn session(ctx: &Ctx) -> Review {
    review::new_session(ctx.app.db(), ctx.student.id, clock::today(), None)
        .await
        .unwrap()
}

#[renox::test]
async fn the_first_day_has_at_most_20_new_cards_and_todays_subject_first() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let math = cards(db, "math", 15).await;
    let bio = cards(db, "biology", 15).await;
    plan_for_today(db, "biology").await;

    let queue = deck::queue_for(db, ctx.student.id, clock::today(), None)
        .await
        .unwrap();
    assert_eq!(queue.items.len(), 20, "30 cards exist, 20 are introduced");
    assert_eq!((queue.due, queue.new), (0, 20));
    let ids: Vec<i64> = queue.items.iter().map(|u| u.c).collect();
    let bio_ids: Vec<i64> = bio.iter().map(|c| c.id).collect();
    assert_eq!(&ids[..15], &bio_ids[..], "all of today's subject first");
    assert_eq!(ids[15], math[0].id, "then the others");

    // The public function the Today page calls.
    assert_eq!(
        deck::due_count(db, ctx.student.id, clock::today())
            .await
            .unwrap(),
        20
    );
    assert_eq!(
        huso::app::flashcards::due_count(db, ctx.student.id, clock::today())
            .await
            .unwrap(),
        20
    );

    ctx.app.acting_as(&ctx.student);
    ctx.app
        .get("/flashcards")
        .await
        .assert_ok()
        .assert_see("Start review (20 cards)");
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_ok()
        .assert_see("1/20");
}

#[renox::test]
async fn grading_good_moves_a_card_to_box_2_and_it_returns_on_the_right_day() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let c = card(db, "math", "basic", "What is 2 + 2?").await;
    ctx.app.acting_as(&ctx.student);
    let start = clock::today();

    let mut live = ctx.app.live(session(&ctx).await);
    live.call_with("reveal", json!([0])).await.assert_ok();
    live.call_with("grade", json!([0, 3])).await.assert_ok();

    let state = CardState::query()
        .where_(CardState::FLASHCARD_ID.eq(c.id))
        .first(db)
        .await
        .unwrap()
        .unwrap();
    assert_eq!(state.r#box, 2);
    assert_eq!(state.due_on, start + Days::days(2), "tomorrow + 1");
    assert_eq!(state.reviews, 1);
    assert_eq!(state.lapses, 0);
    assert_eq!(state.last_grade.as_deref(), Some("good"));
    assert_eq!(state.introduced_on, start);
    let review = CardReview::query().first(db).await.unwrap().unwrap();
    assert_eq!((review.box_before, review.box_after), (1, 2));
    assert_eq!(review.grade, "good");

    // Not due tomorrow ...
    ctx.app.travel(Duration::from_secs(24 * 3600));
    ctx.app.acting_as(&ctx.student);
    assert_eq!(due_now(&ctx).await, 0);
    ctx.app
        .get("/flashcards")
        .await
        .assert_ok()
        .assert_see("Start review (0 cards)");
    // ... but the day after, it is (each trip adds to the last).
    ctx.app.travel(Duration::from_secs(24 * 3600));
    ctx.app.acting_as(&ctx.student);
    assert_eq!(due_now(&ctx).await, 1);
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_ok()
        .assert_see("1/1")
        .assert_see("What is 2 + 2?");
}

#[renox::test]
async fn again_sends_a_card_back_to_box_1_and_counts_a_lapse() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let c = card(db, "physics", "basic", "Unit of force?").await;
    ctx.app.acting_as(&ctx.student);
    let today = clock::today();
    // The card is already in box 4.
    CardState::create(
        db,
        CardState {
            user_id: ctx.student.id,
            flashcard_id: c.id,
            r#box: 4,
            due_on: today,
            introduced_on: today - Days::days(30),
            reviews: 3,
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let mut live = ctx.app.live(session(&ctx).await);
    live.call_with("reveal", json!([0])).await.assert_ok();
    live.call_with("grade", json!([0, 1])).await.assert_ok();
    let state = CardState::query().first(db).await.unwrap().unwrap();
    assert_eq!((state.r#box, state.lapses, state.reviews), (1, 1, 4));
    assert_eq!(state.due_on, today + Days::days(1));
}

#[renox::test]
async fn a_double_press_or_a_stale_page_cannot_grade_a_card_twice() {
    let ctx = setup().await;
    let db = ctx.app.db();
    cards(db, "math", 2).await;
    ctx.app.acting_as(&ctx.student);
    let mut live = ctx.app.live(session(&ctx).await);
    // Grading before the answer is shown does nothing.
    live.call_with("grade", json!([0, 3])).await.assert_ok();
    assert_eq!(CardReview::query().count(db).await.unwrap(), 0);
    live.call_with("reveal", json!([0])).await.assert_ok();
    live.call_with("grade", json!([0, 3])).await.assert_ok();
    // The same key press arrives again for position 0: ignored.
    live.call_with("grade", json!([0, 3])).await.assert_ok();
    assert_eq!(CardReview::query().count(db).await.unwrap(), 1);
    assert_eq!(live.component().pos, 1);
    // A grade that is not 1 to 4 is a bad request.
    live.call_with("reveal", json!([1])).await.assert_ok();
    live.call_with("grade", json!([1, 9]))
        .await
        .assert_status(400);
}

#[renox::test]
async fn finishing_shows_a_summary_and_a_way_back_to_today() {
    let ctx = setup().await;
    let db = ctx.app.db();
    cards(db, "math", 3).await;
    ctx.app.acting_as(&ctx.student);
    let mut live = ctx.app.live(session(&ctx).await);
    for (pos, grade) in [(0, 1), (1, 3), (2, 3)] {
        live.call_with("reveal", json!([pos])).await.assert_ok();
        live.call_with("grade", json!([pos, grade]))
            .await
            .assert_ok();
    }
    let r = live.call("_refresh").await;
    r.assert_ok()
        .assert_see("Session complete")
        .assert_see("You reviewed 3 cards")
        .assert_see("Back to Today");
    assert_eq!(live.component().counts, [1, 0, 2, 0]);
}

#[renox::test]
async fn an_empty_queue_says_there_is_nothing_to_review() {
    let ctx = setup().await;
    ctx.app.acting_as(&ctx.student);
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_ok()
        .assert_see("Nothing to review today");
    ctx.app
        .get("/flashcards")
        .await
        .assert_ok()
        .assert_see("Start review (0 cards)");
}

#[renox::test]
async fn an_occlusion_card_with_three_labels_gives_three_reviews() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let mut c = card(db, "biology", "occlusion", "Name the hidden part.").await;
    c.visual = Some("content/test/cell.svg".to_owned());
    c.save(db).await.unwrap();

    let queue = deck::queue_for(db, ctx.student.id, clock::today(), None)
        .await
        .unwrap();
    let labels: Vec<&str> = queue.items.iter().map(|u| u.l.as_str()).collect();
    assert_eq!(labels, ["Nucleus", "Mitochondrion", "Cell wall"]);

    ctx.app.acting_as(&ctx.student);
    let mut live = ctx.app.live(session(&ctx).await);
    for pos in 0..3 {
        // Before the answer: the label is not in the page, a grey box is.
        let r = live.call("_refresh").await;
        r.assert_see("fc-occluded").assert_dont_see("fc-marked");
        let hidden = labels[pos as usize];
        assert!(
            !r.text().contains(&format!("data-label=\"{hidden}\"")),
            "{hidden} must not be in the page before the answer"
        );
        live.call_with("reveal", json!([pos]))
            .await
            .assert_see(&format!(
                "<strong class=\"fc-label\">{}</strong>",
                labels[pos as usize]
            ));
        live.call_with("grade", json!([pos, 3])).await.assert_ok();
    }
    assert_eq!(CardReview::query().count(db).await.unwrap(), 3);
    let states = CardState::query().get(db).await.unwrap();
    assert_eq!(states.len(), 3, "one state per label");
    let mut got: Vec<_> = states.iter().map(|s| s.label.clone()).collect();
    got.sort();
    assert_eq!(got, ["Cell wall", "Mitochondrion", "Nucleus"]);
    assert!(states.iter().all(|s| s.r#box == 2));
    // The three do not come back today, and the overview counts all three.
    assert_eq!(
        deck::due_count(db, ctx.student.id, clock::today())
            .await
            .unwrap(),
        0
    );
    let deck = Deck::load(db, ctx.student.id).await.unwrap();
    let stats = deck.stats(clock::today());
    let bio = stats.iter().find(|s| s.slug == "biology").unwrap();
    assert_eq!((bio.total, bio.new, bio.boxes[1]), (3, 0, 3));
}

#[renox::test]
async fn cloze_cards_show_an_empty_box_until_the_answer() {
    let ctx = setup().await;
    let db = ctx.app.db();
    card(
        db,
        "biology",
        "cloze",
        "The {{left ventricle}} pumps blood to the body.",
    )
    .await;
    ctx.app.acting_as(&ctx.student);
    let mut live = ctx.app.live(session(&ctx).await);
    let before = live.call("_refresh").await;
    before
        .assert_see("fc-gap")
        .assert_dont_see("left ventricle");
    live.call_with("reveal", json!([0]))
        .await
        .assert_see("fc-gap--open")
        .assert_see("left ventricle");
}

#[renox::test]
async fn order_cards_check_the_clicked_order_and_suggest_a_grade() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let mut c = card(db, "biology", "order", "Put the steps of mitosis in order.").await;
    c.payload = Json(json!({ "items": ["Prophase", "Metaphase", "Anaphase", "Telophase"] }));
    c.save(db).await.unwrap();
    ctx.app.acting_as(&ctx.student);

    // The shuffled position of each item, read from the page data.
    let perm = huso::app::flashcards::card::shuffled(4, c.id as u64);
    assert_ne!(perm, [0, 1, 2, 3]);
    let position_of = |item: usize| perm.iter().position(|p| *p == item).unwrap();

    // Right order: items 0, 1, 2, 3.
    let mut live = ctx.app.live(session(&ctx).await);
    for item in 0..4 {
        live.call_with("pick", json!([0, position_of(item)]))
            .await
            .assert_ok();
    }
    let r = live.call("_refresh").await;
    r.assert_see("Right! That is the correct order.");
    assert!(live.component().revealed, "the last click shows the answer");
    live.call_with("grade", json!([0, 3])).await.assert_ok();

    // Wrong order: starts with item 1.
    let ctx2 = setup().await;
    let db2 = ctx2.app.db();
    let mut c2 = card(db2, "biology", "order", "Put the steps in order.").await;
    c2.payload = Json(json!({ "items": ["A", "B", "C"] }));
    c2.save(db2).await.unwrap();
    ctx2.app.acting_as(&ctx2.student);
    let perm2 = huso::app::flashcards::card::shuffled(3, c2.id as u64);
    let pos2 = |item: usize| perm2.iter().position(|p| *p == item).unwrap();
    let mut live2 = ctx2.app.live(session(&ctx2).await);
    for item in [1, 0, 2] {
        live2
            .call_with("pick", json!([0, pos2(item)]))
            .await
            .assert_ok();
    }
    live2
        .call("_refresh")
        .await
        .assert_see("Not quite. The right order is:");
}

#[renox::test]
async fn match_cards_count_wrong_tries_and_finish_when_everything_is_paired() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let mut c = card(db, "chemistry", "match", "Match the symbol to the element.").await;
    c.payload = Json(json!({ "pairs": [["H", "Hydrogen"], ["O", "Oxygen"], ["Na", "Sodium"]] }));
    c.save(db).await.unwrap();
    ctx.app.acting_as(&ctx.student);
    let perm = huso::app::flashcards::card::shuffled(3, c.id as u64 ^ 0x5bd1_e995);
    let right_pos = |pair: usize| perm.iter().position(|p| *p == pair).unwrap();

    let mut live = ctx.app.live(session(&ctx).await);
    // A wrong try: H with Oxygen.
    live.call_with("choose_left", json!([0, 0]))
        .await
        .assert_ok();
    live.call_with("choose_right", json!([0, right_pos(1)]))
        .await
        .assert_ok();
    assert_eq!(live.component().mistakes, 1);
    assert!(live.component().matched.is_empty());
    for pair in 0..3 {
        live.call_with("choose_left", json!([0, pair]))
            .await
            .assert_ok();
        live.call_with("choose_right", json!([0, right_pos(pair)]))
            .await
            .assert_ok();
    }
    assert!(live.component().revealed);
    live.call("_refresh")
        .await
        .assert_see("Matched, with 1 wrong tries.")
        .assert_see("Sodium");
}

#[renox::test]
async fn only_the_student_reviews() {
    let ctx = setup().await;
    let db = ctx.app.db();
    cards(db, "math", 2).await;
    let session = session(&ctx).await;

    ctx.app.acting_as(&ctx.parent);
    ctx.app.get("/flashcards/review").await.assert_forbidden();
    let mut live = ctx.app.live(session.clone());
    live.call_with("reveal", json!([0]))
        .await
        .assert_forbidden();
    live.call_with("grade", json!([0, 3]))
        .await
        .assert_forbidden();
    assert_eq!(CardReview::query().count(db).await.unwrap(), 0);

    // A guest is sent to the login page.
    let guest = TestApp::new(app()).await;
    guest
        .get("/flashcards/review")
        .await
        .assert_redirect("/login");
    // The overview is public: a guest only sees the deck.
    guest.get("/flashcards").await.assert_ok();
}

#[renox::test]
async fn the_parent_sees_the_students_numbers_read_only() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let c = card(db, "math", "basic", "Parent sees this").await;
    CardState::create(
        db,
        CardState {
            user_id: ctx.student.id,
            flashcard_id: c.id,
            r#box: 3,
            due_on: clock::today(),
            introduced_on: clock::today() - Days::days(3),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    ctx.app.acting_as(&ctx.parent);
    ctx.app
        .get("/flashcards")
        .await
        .assert_ok()
        .assert_see("Mathematics")
        .assert_see("Only the student does the reviews")
        .assert_dont_see("Start review");
}

#[renox::test]
async fn the_overview_has_a_row_per_subject_a_chart_and_a_subject_filter() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let math = cards(db, "math", 2).await;
    cards(db, "earth", 1).await;
    ctx.app.acting_as(&ctx.student);
    // No chart before anything is started.
    ctx.app
        .get("/flashcards")
        .await
        .assert_dont_see("boxes-chart");
    CardState::create(
        db,
        CardState {
            user_id: ctx.student.id,
            flashcard_id: math[0].id,
            r#box: 2,
            due_on: clock::today() + Days::days(2),
            introduced_on: clock::today() - Days::days(1),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    let all = ctx.app.get("/flashcards").await;
    all.assert_ok()
        .assert_view("flashcards/index.html")
        .assert_see("Mathematics")
        .assert_see("Earth Science")
        .assert_see("boxes-chart")
        .assert_see("Start review (2 cards)");
    let math = ctx.app.get("/flashcards?subject=math").await;
    math.assert_ok()
        .assert_see("Start review (1 cards)")
        .assert_dont_see("Earth Science</rx-column>");
    // The review respects the filter.
    ctx.app
        .get("/flashcards/review?subject=earth")
        .await
        .assert_ok()
        .assert_see("1/1");
    // An unknown subject means all.
    ctx.app
        .get("/flashcards?subject=nope")
        .await
        .assert_see("Start review (2 cards)");
}

#[renox::test]
async fn the_shortcuts_are_bound_to_space_and_the_keys_1_to_4() {
    let ctx = setup().await;
    let db = ctx.app.db();
    cards(db, "math", 1).await;
    ctx.app.acting_as(&ctx.student);
    let page = ctx.app.get("/flashcards/review").await;
    page.assert_ok().assert_see("data-rx-key=\"space\"");
    let mut live = ctx.app.live(session(&ctx).await);
    live.call_with("reveal", json!([0]))
        .await
        .assert_see("data-rx-key=\"1\"")
        .assert_see("data-rx-key=\"2\"")
        .assert_see("data-rx-key=\"3\"")
        .assert_see("data-rx-key=\"4\"")
        .assert_see("tomorrow")
        .assert_see("2 days")
        .assert_see("4 days")
        .assert_dont_see("data-rx-key=\"space\"");
}

#[renox::test]
async fn the_review_card_border_uses_the_subject_colour_from_the_database() {
    let ctx = setup().await;
    let db = ctx.app.db();
    cards(db, "biology", 1).await;
    ctx.app.acting_as(&ctx.student);
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_ok()
        .assert_see("--fc-color: #16a34a");
}

// ----- Manual cards ---------------------------------------------------------------------

async fn add_manual(ctx: &Ctx, topic: i64, image: bool) -> TestResponseLike {
    let topic = topic.to_string();
    let fields = [
        ("subject", "biology"),
        ("topic", topic.as_str()),
        ("front", "What carries oxygen in blood?"),
        ("back", "Haemoglobin in red blood cells."),
        ("sketch_prompt", ""),
    ];
    let files: Vec<(&str, &str, &[u8])> = if image {
        vec![("image", "rbc.png", PNG)]
    } else {
        vec![]
    };
    ctx.app
        .post_multipart("/flashcards/manual", &fields, &files)
        .await
}

type TestResponseLike = renox::testing::TestResponse;

#[renox::test]
async fn a_manual_card_with_an_uploaded_image_shows_in_the_review() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let topic = subtopic(db, "biology").await;
    ctx.app.acting_as(&ctx.student);
    add_manual(&ctx, topic.id, true)
        .await
        .assert_redirect("/flashcards");

    let card = Flashcard::query().first(db).await.unwrap().unwrap();
    assert_eq!(card.origin, "manual");
    assert_eq!(card.card_type, "basic");
    assert_eq!(card.topic_id, topic.id);
    let url = card.visual.clone().unwrap();
    assert!(
        url.starts_with("/storage/flashcards/") && url.ends_with(".png"),
        "{url}"
    );

    ctx.app
        .get("/flashcards")
        .await
        .assert_ok()
        .assert_see("What carries oxygen in blood?")
        .assert_see("Start review (1 cards)");
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_ok()
        .assert_see("1/1")
        .assert_see(&format!("<img src=\"{url}\""))
        .assert_see("What carries oxygen in blood?");
    // The file is served.
    ctx.app.get(&url).await.assert_ok();
}

#[renox::test]
async fn a_manual_card_needs_a_picture_or_a_drawing_prompt() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let topic = subtopic(db, "biology").await;
    ctx.app.acting_as(&ctx.student);
    let r = add_manual(&ctx, topic.id, false).await;
    assert!(r.status == 303 || r.status == 422, "status {}", r.status);
    assert_eq!(Flashcard::query().count(db).await.unwrap(), 0);

    // With a drawing prompt instead of a picture, it works.
    let t = topic.id.to_string();
    ctx.app
        .post_multipart(
            "/flashcards/manual",
            &[
                ("topic", t.as_str()),
                ("front", "Heart"),
                ("back", "Four chambers"),
                (
                    "sketch_prompt",
                    "Draw the heart and label the four chambers.",
                ),
            ],
            &[],
        )
        .await
        .assert_redirect("/flashcards");
    let card = Flashcard::query().first(db).await.unwrap().unwrap();
    assert_eq!(card.visual, None);
    ctx.app
        .get("/flashcards/review")
        .await
        .assert_see("Draw it on paper first:")
        .assert_see("Draw the heart and label the four chambers.");
}

#[renox::test]
async fn manual_cards_can_be_changed_deleted_and_only_manual_ones() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let topic = subtopic(db, "biology").await;
    let content_card = card(db, "biology", "basic", "From the files").await;
    ctx.app.acting_as(&ctx.parent); // the parent may add and change cards too
    add_manual(&ctx, topic.id, true)
        .await
        .assert_redirect("/flashcards");
    let manual = Flashcard::query()
        .where_(Flashcard::ORIGIN.eq("manual"))
        .first(db)
        .await
        .unwrap()
        .unwrap();

    ctx.app
        .get(&format!("/flashcards/manual/{}/edit", manual.id))
        .await
        .assert_ok()
        .assert_see("Edit card")
        .assert_see("What carries oxygen in blood?");
    let t = topic.id.to_string();
    ctx.app
        .post_multipart(
            &format!("/flashcards/manual/{}", manual.id),
            &[
                ("topic", t.as_str()),
                ("front", "What carries oxygen?"),
                ("back", "Haemoglobin."),
                ("sketch_prompt", ""),
            ],
            &[],
        )
        .await
        .assert_redirect("/flashcards");
    let changed = Flashcard::find(db, manual.id).await.unwrap().unwrap();
    assert_eq!(changed.front, "What carries oxygen?");
    assert_eq!(changed.visual, manual.visual, "the picture stays");

    // Cards from the content files cannot be edited or deleted here.
    ctx.app
        .get(&format!("/flashcards/manual/{}/edit", content_card.id))
        .await
        .assert_not_found();
    ctx.app
        .delete(&format!("/flashcards/manual/{}", content_card.id))
        .await
        .assert_not_found();

    ctx.app
        .delete(&format!("/flashcards/manual/{}", manual.id))
        .await
        .assert_redirect("/flashcards");
    assert!(Flashcard::find(db, manual.id).await.unwrap().is_none());
    assert!(
        Flashcard::find(db, content_card.id)
            .await
            .unwrap()
            .is_some()
    );
}

#[renox::test]
async fn the_subtopic_list_follows_the_chosen_subject() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let bio = subtopic(db, "biology").await;
    let math = subtopic(db, "math").await;
    ctx.app.acting_as(&ctx.student);
    let r = ctx
        .app
        .htmx()
        .get("/flashcards/manual/topics?subject=biology")
        .await;
    r.assert_ok()
        .assert_see(&bio.name)
        .assert_dont_see(&format!(">{}<", math.name));
    ctx.app
        .get("/flashcards/manual/new")
        .await
        .assert_ok()
        .assert_see("New card")
        .assert_see("flashcards/manual/topics");
}

#[renox::test]
async fn a_card_must_hang_on_a_subtopic() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let bio = subtopic(db, "biology").await;
    let top = Topic::find(db, bio.parent_id.unwrap())
        .await
        .unwrap()
        .unwrap();
    ctx.app.acting_as(&ctx.student);
    let r = add_manual(&ctx, top.id, true).await;
    assert!(r.status == 303 || r.status == 422, "status {}", r.status);
    assert_eq!(Flashcard::query().count(db).await.unwrap(), 0);
}

#[renox::test]
async fn deck_numbers_do_not_mix_up_students() {
    let ctx = setup().await;
    let db = ctx.app.db();
    let c = card(db, "math", "basic", "Q").await;
    CardState::create(
        db,
        CardState {
            user_id: ctx.parent.id,
            flashcard_id: c.id,
            r#box: 5,
            due_on: NaiveDate::from_ymd_opt(2030, 1, 1).unwrap(),
            introduced_on: clock::today(),
            ..Default::default()
        },
    )
    .await
    .unwrap();
    // Someone else's state does not count for the student: the card is still new.
    assert_eq!(
        deck::due_count(db, ctx.student.id, clock::today())
            .await
            .unwrap(),
        1
    );
}

#[renox::test]
async fn the_models_match_the_schema_and_the_views_compile() {
    let ctx = setup().await;
    ctx.app.assert_models_match_schema().await;
    ctx.app.assert_views_compile();
}
