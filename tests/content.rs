use huso::app::content::files::{load_all, validate};
use std::path::Path;

#[test]
fn the_real_content_is_valid() {
    let bundle = load_all(Path::new(env!("CARGO_MANIFEST_DIR"))).expect("content files parse");
    let errors = validate(&bundle);
    assert!(errors.is_empty(), "{errors:#?}");
}

#[test]
fn a_broken_fixture_produces_the_expected_errors() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/content_bad");
    let bundle = load_all(&root).expect("fixture parses");
    let errors = validate(&bundle).join("\n");
    for expected in [
        "plan: expected 35 days, found 2",
        "gap or disorder",
        "unknown phase `party`",
        "unknown subject `cooking`",
        "duplicate flashcard id `physics-0001`",
        "a cloze card needs a {{gap}}",
        "`physics.mechanics.nothing` is not a subtopic",
        "an order card needs at least 3 `items`",
        "needs a `visual` or a `sketch_prompt`",
        "`physics.mechanics.ghost` is not a subtopic",
        "difficulty must be 1-3, found 4",
        "two choices are identical",
        "answer `F` is not one of A-E",
        "source must be `original`",
        "visual `content/physics/missing.svg` does not exist",
    ] {
        assert!(
            errors.contains(expected),
            "missing `{expected}` in:\n{errors}"
        );
    }
}

#[test]
fn every_material_file_has_a_valid_slug_and_five_check_questions() {
    let bundle = load_all(Path::new(env!("CARGO_MANIFEST_DIR"))).expect("content files parse");
    assert!(
        bundle.lessons.len() >= 40,
        "{} lessons",
        bundle.lessons.len()
    );
    for lesson in &bundle.lessons {
        assert!(
            lesson.problems.is_empty(),
            "{}: {:?}",
            lesson.path,
            lesson.problems
        );
        assert_eq!(lesson.questions.len(), 5, "{}", lesson.path);
        assert!(
            lesson
                .questions
                .iter()
                .all(|q| q.choices.len() == 5 && !q.answer.is_empty())
        );
    }
}

#[test]
fn a_lesson_with_a_wrong_slug_gives_a_clear_error() {
    use huso::app::content::lesson_file::LessonFile;
    let mut bundle = load_all(Path::new(env!("CARGO_MANIFEST_DIR"))).expect("content files parse");
    bundle.lessons.push(LessonFile {
        path: "materi/biology/oops.md".into(),
        subject: "biology".into(),
        slug: "biology.cell.nothing".into(),
        title: "Oops".into(),
        ..Default::default()
    });
    bundle.lessons.push(LessonFile {
        path: "materi/physics/wrong-folder.md".into(),
        subject: "physics".into(),
        slug: "biology.cell.division".into(),
        title: "Wrong folder".into(),
        ..Default::default()
    });
    let errors = validate(&bundle).join("\n");
    assert!(
        errors.contains("materi/biology/oops.md: `biology.cell.nothing` is not a subtopic"),
        "{errors}"
    );
    assert!(
        errors.contains("is not in the folder `materi/physics`"),
        "{errors}"
    );
    assert!(
        errors.contains("a second lesson for `biology.cell.division`"),
        "{errors}"
    );
}
