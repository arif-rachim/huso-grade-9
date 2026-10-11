use huso::app;
use huso::app::content::models::{Question, Subject, Topic};
use huso::app::practice::engine;
use huso::app::practice::models::{Answer, Attempt};
use renox::prelude::*;
use renox::testing::TestApp;
use std::time::Duration;

const SUBJECTS: [(&str, &str, &str); 5] = [
    ("math", "Mathematics", "#2563eb"),
    ("physics", "Physics", "#dc2626"),
    ("chemistry", "Chemistry", "#ca8a04"),
    ("biology", "Biology", "#16a34a"),
    ("earth", "Earth Science", "#92400e"),
];

struct Fixture {
    app: TestApp,
    student: User,
    parent: User,
}

/// An app with the two accounts and `per_subject` questions in each of the five subjects.
/// Every question's key is "A"; its stem is `Q-<subject>-<n>` and its explanation `Why-<subject>-<n>`.
async fn fixture(per_subject: usize) -> Fixture {
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
    for (i, (slug, name, color)) in SUBJECTS.iter().enumerate() {
        let subject = Subject::create(
            app.db(),
            Subject {
                slug: (*slug).into(),
                name: (*name).into(),
                color: (*color).into(),
                emoji: "*".into(),
                position: i as i64,
                ..Default::default()
            },
        )
        .await
        .unwrap();
        let topic = Topic::create(
            app.db(),
            Topic {
                slug: (*slug).into(),
                subject_id: subject.id,
                name: format!("{name} topic"),
                ..Default::default()
            },
        )
        .await
        .unwrap();
        let sub = Topic::create(
            app.db(),
            Topic {
                slug: format!("{slug}.sub"),
                subject_id: subject.id,
                parent_id: Some(topic.id),
                name: format!("{name} subtopic"),
                ..Default::default()
            },
        )
        .await
        .unwrap();
        for n in 1..=per_subject {
            Question::create(
                app.db(),
                Question {
                    key: format!("{slug}-{n:04}"),
                    topic_id: sub.id,
                    difficulty: 1 + (n as i64 % 3),
                    stem: format!("Q-{slug}-{n}"),
                    choice_a: "first".into(),
                    choice_b: "second".into(),
                    choice_c: "third".into(),
                    choice_d: "fourth".into(),
                    choice_e: "fifth".into(),
                    answer: "A".into(),
                    explanation: format!("Why-{slug}-{n}"),
                    source: "original".into(),
                    ..Default::default()
                },
            )
            .await
            .unwrap();
        }
    }
    Fixture {
        app,
        student,
        parent,
    }
}

async fn subtopic_id(f: &Fixture, slug: &str) -> i64 {
    Topic::query()
        .where_(Topic::SLUG.eq(format!("{slug}.sub").as_str()))
        .first(f.app.db())
        .await
        .unwrap()
        .unwrap()
        .id
}

/// Start a practice as the student and return its attempt.
async fn start(f: &Fixture, form: &[(&str, &str)]) -> Attempt {
    f.app.acting_as(&f.student);
    let res = f.app.post("/practice", form).await;
    res.assert_status(303);
    Attempt::query()
        .order_by_desc(Attempt::ID)
        .first(f.app.db())
        .await
        .unwrap()
        .expect("an attempt was made")
}

async fn answers(f: &Fixture, attempt: &Attempt) -> Vec<Answer> {
    Answer::query()
        .where_(Answer::ATTEMPT_ID.eq(attempt.id))
        .order_by(Answer::POSITION)
        .get(f.app.db())
        .await
        .unwrap()
}

async fn reload(f: &Fixture, attempt: &Attempt) -> Attempt {
    Attempt::find(f.app.db(), attempt.id)
        .await
        .unwrap()
        .unwrap()
}

async fn answer(f: &Fixture, attempt: &Attempt, number: i64, choice: &str, guessed: bool) {
    f.app.acting_as(&f.student);
    f.app
        .post(
            &format!("/practice/{}/answer", attempt.id),
            &[
                ("q", &number.to_string()),
                ("choice", choice),
                ("guessed", if guessed { "true" } else { "false" }),
                ("skip", "false"),
            ],
        )
        .await;
}

#[renox::test]
async fn the_practice_page_lists_the_modes() {
    let f = fixture(3).await;
    f.app.acting_as(&f.student);
    f.app
        .get("/practice")
        .await
        .assert_ok()
        .assert_see("Topic")
        .assert_see("Sprint")
        .assert_see("Mixed")
        .assert_see("Round 1 simulation")
        .assert_dont_see("Redo wrong questions");
}

#[renox::test]
async fn topic_mode_explains_each_answer_at_once() {
    let f = fixture(12).await;
    let topic = subtopic_id(&f, "physics").await;
    let attempt = start(&f, &[("mode", "topic"), ("topic", &topic.to_string())]).await;
    assert_eq!(attempt.len(), 10, "topic practice has 10 questions");
    assert_eq!(attempt.time_limit_secs, None, "and no timer");

    f.app.acting_as(&f.student);
    let page = f.app.get(&format!("/practice/{}", attempt.id)).await;
    page.assert_ok().assert_dont_see("Why-physics");

    answer(&f, &attempt, 1, "B", false).await;
    let res = f.app.get(&format!("/practice/{}?q=1", attempt.id)).await;
    res.assert_ok()
        .assert_see("Why-physics")
        .assert_see("The answer is A");

    // The first answer is final in topic mode.
    answer(&f, &attempt, 1, "A", false).await;
    let first = &answers(&f, &attempt).await[0];
    assert_eq!(first.choice.as_deref(), Some("B"));
    assert!(!first.is_correct);
}

#[renox::test]
async fn sprint_and_simulation_hold_the_explanations_back_until_the_end() {
    let f = fixture(6).await;
    let sprint = start(
        &f,
        &[("mode", "sprint"), ("subject", "biology"), ("count", "5")],
    )
    .await;
    assert_eq!(sprint.len(), 5);
    // Biology: 0.9 minute per question.
    assert_eq!(sprint.time_limit_secs, Some(5 * 54));
    answer(&f, &sprint, 1, "A", false).await;
    f.app
        .get(&format!("/practice/{}?q=1", sprint.id))
        .await
        .assert_ok()
        .assert_dont_see("Why-biology")
        .assert_dont_see("Correct!");

    let sim = start(&f, &[("mode", "simulation")]).await;
    answer(&f, &sim, 1, "A", false).await;
    f.app
        .get(&format!("/practice/{}?q=1", sim.id))
        .await
        .assert_ok()
        .assert_dont_see("Why-math");

    // After finishing, the result shows the explanations.
    f.app
        .post(&format!("/practice/{}/finish", sprint.id), &[])
        .await
        .assert_redirect(&format!("/practice/{}/result", sprint.id));
    f.app
        .get(&format!("/practice/{}/result", sprint.id))
        .await
        .assert_ok()
        .assert_see("Why-biology");
}

#[renox::test]
async fn sprint_time_depends_on_the_subject() {
    assert_eq!(engine::sprint_secs_per_question("math"), 180);
    assert_eq!(engine::sprint_secs_per_question("physics"), 60);
    assert_eq!(engine::sprint_secs_per_question("chemistry"), 60);
    assert_eq!(engine::sprint_secs_per_question("earth"), 54);
}

#[renox::test]
async fn when_the_timer_runs_out_the_rest_is_blank_and_locked() {
    let f = fixture(6).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "physics"), ("count", "4")],
    )
    .await;
    assert_eq!(attempt.time_limit_secs, Some(240));
    answer(&f, &attempt, 1, "A", false).await;
    f.app
        .get(&format!("/practice/{}", attempt.id))
        .await
        .assert_ok();

    f.app.travel(Duration::from_secs(241));
    // Opening the page closes the attempt and goes to the result.
    f.app
        .get(&format!("/practice/{}", attempt.id))
        .await
        .assert_redirect(&format!("/practice/{}/result", attempt.id));
    let rows = answers(&f, &attempt).await;
    assert_eq!(rows.len(), 4);
    assert_eq!(
        rows[0].choice.as_deref(),
        Some("A"),
        "the answer in time stays"
    );
    for r in &rows[1..] {
        assert!(r.choice.is_none(), "blank after the deadline");
        assert!(!r.is_correct);
        assert!(r.answered_at.is_some());
    }
    assert!(reload(&f, &attempt).await.is_finished());

    // A late answer is refused and changes nothing.
    answer(&f, &attempt, 2, "A", false).await;
    assert!(answers(&f, &attempt).await[1].choice.is_none());
}

#[renox::test]
async fn the_clock_is_the_servers_even_if_nobody_opens_the_page() {
    let f = fixture(6).await;
    let attempt = start(&f, &[("mode", "mixed")]).await;
    assert_eq!(attempt.time_limit_secs, Some(20 * 60));
    f.app.travel(Duration::from_secs(21 * 60));
    // The index page also closes the attempt that ran out while the laptop was shut.
    f.app.acting_as(&f.student);
    f.app.get("/practice").await.assert_ok();
    assert!(reload(&f, &attempt).await.is_finished());
}

#[renox::test]
async fn the_guessed_marker_is_saved_and_shown() {
    let f = fixture(5).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "chemistry"), ("count", "3")],
    )
    .await;
    answer(&f, &attempt, 1, "A", true).await; // right, but a guess
    answer(&f, &attempt, 2, "B", false).await; // wrong
    answer(&f, &attempt, 3, "A", false).await; // right, sure
    f.app
        .post(&format!("/practice/{}/finish", attempt.id), &[])
        .await;

    let rows = answers(&f, &attempt).await;
    assert!(rows[0].guessed && rows[0].is_correct);
    assert!(!rows[1].guessed && !rows[1].is_correct);
    assert!(!rows[2].guessed && rows[2].is_correct);
    // What the Error Log will read.
    assert!(rows[0].needs_review() && rows[1].needs_review() && !rows[2].needs_review());

    f.app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .assert_ok()
        .assert_see("Guessed")
        .assert_see("→ added to Error Log");
    // Two of the three questions are in the Error Log.
    let text = f
        .app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .text();
    assert_eq!(text.matches("→ added to Error Log").count(), 2);
}

#[renox::test]
async fn skipping_records_a_blank_without_a_guess() {
    let f = fixture(4).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "math"), ("count", "2")],
    )
    .await;
    f.app.acting_as(&f.student);
    f.app
        .post(
            &format!("/practice/{}/answer", attempt.id),
            &[
                ("q", "1"),
                ("choice", "C"),
                ("guessed", "true"),
                ("skip", "true"),
            ],
        )
        .await
        .assert_status(303);
    let first = &answers(&f, &attempt).await[0];
    // A skip wins over a choice that was left selected, and a blank cannot be a guess.
    assert!(first.choice.is_none() && first.answered_at.is_some() && !first.guessed);
}

#[renox::test]
async fn the_simulation_adds_up_the_best_four_subjects() {
    let f = fixture(4).await;
    let sim = start(&f, &[("mode", "simulation")]).await;
    assert_eq!(sim.sections.len(), 5);
    assert_eq!(
        sim.len(),
        20,
        "4 questions in each of 5 sections (all there are)"
    );
    for s in sim.sections.iter() {
        assert_eq!(s.secs, 36 * 60);
    }

    // math 4/4 right, physics 3/4, chemistry 0/4 (all wrong), biology 2/4, earth 4/4.
    let plan: [&[&str]; 5] = [
        &["A", "A", "A", "A"],
        &["A", "A", "A", "B"],
        &["B", "B", "B", "B"],
        &["A", "A", "B", "B"],
        &["A", "A", "A", "A"],
    ];
    for (s, choices) in plan.iter().enumerate() {
        for (i, c) in choices.iter().enumerate() {
            let number = (s * 4 + i + 1) as i64;
            answer(&f, &sim, number, c, false).await;
        }
        f.app
            .post(&format!("/practice/{}/finish", sim.id), &[])
            .await;
    }
    assert!(reload(&f, &sim).await.is_finished());

    f.app.acting_as(&f.student);
    let res = f.app.get(&format!("/practice/{}/result", sim.id)).await;
    res.assert_ok()
        .assert_see("Best 4 subjects")
        .assert_see("Dropped: Chemistry")
        // 100 + 75 + 50 + 100 = 325
        .assert_see("325.0 / 400");
}

#[renox::test]
async fn simulation_sections_have_their_own_timers() {
    let f = fixture(3).await;
    let sim = start(&f, &[("mode", "simulation")]).await;
    answer(&f, &sim, 1, "A", false).await;

    // 37 minutes: section 1 (math) is over, section 2 (physics) has started.
    f.app.travel(Duration::from_secs(37 * 60));
    f.app.acting_as(&f.student);
    f.app
        .get(&format!("/practice/{}", sim.id))
        .await
        .assert_ok()
        .assert_see("Section 2 of 5");
    let now = reload(&f, &sim).await;
    assert_eq!(now.section, 1);
    let rows = answers(&f, &sim).await;
    assert_eq!(rows[0].choice.as_deref(), Some("A"));
    assert!(
        rows[1].choice.is_none() && rows[1].answered_at.is_some(),
        "math is blank"
    );
    assert!(rows[2].answered_at.is_some());
    assert!(rows[3].answered_at.is_none(), "physics is still open");

    // Math is locked for good; physics can be answered.
    answer(&f, &sim, 2, "A", false).await;
    assert!(answers(&f, &sim).await[1].choice.is_none());
    answer(&f, &sim, 4, "A", false).await;
    assert_eq!(answers(&f, &sim).await[3].choice.as_deref(), Some("A"));

    // Long after the last section: the whole simulation is over.
    f.app.travel(Duration::from_secs(5 * 36 * 60));
    f.app.acting_as(&f.student);
    f.app
        .get(&format!("/practice/{}", sim.id))
        .await
        .assert_redirect(&format!("/practice/{}/result", sim.id));
    let rows = answers(&f, &sim).await;
    assert!(rows.iter().all(|r| r.answered_at.is_some()));
}

#[renox::test]
async fn a_refresh_keeps_the_same_questions() {
    let f = fixture(30).await;
    let attempt = start(&f, &[("mode", "mixed")]).await;
    assert_eq!(attempt.len(), 15);
    // Three questions of each subject.
    let rows = engine::load_rows(f.app.db(), attempt.id).await.unwrap();
    for (slug, _, _) in SUBJECTS {
        assert_eq!(
            rows.iter().filter(|r| r.subject.slug == slug).count(),
            3,
            "{slug}"
        );
    }
    f.app.acting_as(&f.student);
    let first = f
        .app
        .get(&format!("/practice/{}?q=4", attempt.id))
        .await
        .text();
    let again = f
        .app
        .get(&format!("/practice/{}?q=4", attempt.id))
        .await
        .text();
    let stem = |t: &str| {
        t.split("Q-")
            .nth(1)
            .map(|s| s[..12.min(s.len())].to_owned())
    };
    assert_eq!(stem(&first), stem(&again));
    assert_eq!(
        reload(&f, &attempt).await.question_ids.0,
        attempt.question_ids.0
    );
    // Difficulty never goes down within one attempt.
    let ds: Vec<i64> = rows.iter().map(|r| r.question.difficulty).collect();
    assert!(ds.windows(2).all(|w| w[0] <= w[1]), "{ds:?}");
}

#[renox::test]
async fn questions_never_answered_come_first_then_the_wrong_ones() {
    let f = fixture(6).await;
    // Answer 3 of the 6 physics questions in a first sprint: 2 wrong, 1 right.
    let first = start(
        &f,
        &[("mode", "sprint"), ("subject", "physics"), ("count", "3")],
    )
    .await;
    answer(&f, &first, 1, "B", false).await;
    answer(&f, &first, 2, "B", false).await;
    answer(&f, &first, 3, "A", false).await;
    f.app
        .post(&format!("/practice/{}/finish", first.id), &[])
        .await;
    let seen: Vec<i64> = first.question_ids.0.clone();

    // A sprint of 3 now takes the 3 questions it has never shown.
    let second = start(
        &f,
        &[("mode", "sprint"), ("subject", "physics"), ("count", "3")],
    )
    .await;
    assert!(second.question_ids.iter().all(|id| !seen.contains(id)));
    answer(&f, &second, 1, "A", false).await;
    f.app
        .post(&format!("/practice/{}/finish", second.id), &[])
        .await;

    // Six questions: two answered right, two wrong, two never answered (a blank is not an
    // answer). A sprint of 5 takes the four that are not "answered right" and one of the others.
    let third = start(
        &f,
        &[("mode", "sprint"), ("subject", "physics"), ("count", "5")],
    )
    .await;
    let right_before = [seen[2], second.question_ids[0]];
    let included_right = third
        .question_ids
        .iter()
        .filter(|id| right_before.contains(id))
        .count();
    assert_eq!(
        included_right, 1,
        "only one of the two answered right is let in"
    );
}

#[renox::test]
async fn nothing_to_practice_says_so() {
    let f = fixture(0).await;
    f.app.acting_as(&f.student);
    let res = f.app.post("/practice", &[("mode", "simulation")]).await;
    res.assert_redirect("/practice");
    assert_eq!(Attempt::query().count(f.app.db()).await.unwrap(), 0);
}

#[renox::test]
async fn the_parent_can_read_results_but_not_start_or_answer() {
    let f = fixture(4).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "earth"), ("count", "2")],
    )
    .await;
    answer(&f, &attempt, 1, "A", false).await;
    f.app
        .post(&format!("/practice/{}/finish", attempt.id), &[])
        .await;

    f.app.acting_as(&f.parent);
    f.app
        .get("/practice")
        .await
        .assert_ok()
        .assert_see("Recent practices");
    f.app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .assert_ok()
        .assert_see("Why-earth");
    f.app
        .post("/practice", &[("mode", "mixed")])
        .await
        .assert_forbidden();
    f.app
        .post(
            &format!("/practice/{}/answer", attempt.id),
            &[("q", "2"), ("choice", "A")],
        )
        .await
        .assert_forbidden();
    assert!(answers(&f, &attempt).await[1].choice.is_none());
    f.app
        .post(&format!("/practice/{}/finish", attempt.id), &[])
        .await
        .assert_forbidden();
}

#[renox::test]
async fn an_unfinished_attempt_has_no_result_for_the_parent() {
    let f = fixture(4).await;
    let attempt = start(&f, &[("mode", "mixed")]).await;
    f.app.acting_as(&f.parent);
    f.app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .assert_status(409);
    // The student is sent back to the question instead.
    f.app.acting_as(&f.student);
    f.app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .assert_redirect(&format!("/practice/{}", attempt.id));
}

#[renox::test]
async fn finishing_fills_in_every_answer_and_can_be_repeated() {
    let f = fixture(5).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "math"), ("count", "5")],
    )
    .await;
    answer(&f, &attempt, 2, "A", false).await;
    let done = engine::finish_attempt(f.app.db(), attempt.id)
        .await
        .unwrap();
    let again = engine::finish_attempt(f.app.db(), attempt.id)
        .await
        .unwrap();
    assert_eq!(done.finished_at, again.finished_at);
    let rows = answers(&f, &attempt).await;
    assert_eq!(rows.len(), 5);
    assert!(rows.iter().all(|r| r.answered_at.is_some()));
    assert_eq!(rows.iter().filter(|r| r.is_correct).count(), 1);
    assert_eq!(rows.iter().filter(|r| r.is_blank()).count(), 4);
}

#[renox::test]
async fn nobody_else_can_open_an_attempt() {
    let f = fixture(3).await;
    let attempt = start(&f, &[("mode", "mixed")]).await;
    let other = User::register(f.app.db(), "Eve", "eve@example.com", "password123")
        .await
        .unwrap();
    f.app.acting_as(&other);
    f.app
        .get(&format!("/practice/{}", attempt.id))
        .await
        .assert_not_found();
    f.app
        .get(&format!("/practice/{}/result", attempt.id))
        .await
        .assert_not_found();
}

#[renox::test]
async fn the_question_screen_wires_up_the_keyboard() {
    let f = fixture(3).await;
    let attempt = start(
        &f,
        &[("mode", "sprint"), ("subject", "math"), ("count", "3")],
    )
    .await;
    f.app.acting_as(&f.student);
    f.app
        .get(&format!("/practice/{}", attempt.id))
        .await
        .assert_ok()
        .assert_see("keydown.window")
        .assert_see("I guessed")
        .assert_see("Skip");
}

#[renox::test]
async fn the_practice_views_compile() {
    let app = TestApp::new(app()).await;
    app.assert_views_compile();
}
