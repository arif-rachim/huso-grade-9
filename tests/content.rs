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
