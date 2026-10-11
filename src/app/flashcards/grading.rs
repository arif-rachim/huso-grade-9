//! Writing a review: the card's new box and due date, and a line in the review history.

use super::leitner::{self, Grade, Outcome};
use super::models::{CardReview, CardState};
use renox::chrono::NaiveDate;
use renox::prelude::*;

/// The state of one card (or one label) for a student, if it was ever reviewed.
pub async fn find_state(
    db: &Db,
    user_id: i64,
    flashcard_id: i64,
    label: &str,
) -> Result<Option<CardState>> {
    CardState::query()
        .where_(CardState::USER_ID.eq(user_id))
        .where_(CardState::FLASHCARD_ID.eq(flashcard_id))
        .where_(CardState::LABEL.eq(label))
        .first(db)
        .await
}

/// Grades one card for the student on `today`. A card that was never reviewed starts in
/// box 1; the result says where it goes and when it is due again.
pub async fn record(
    db: &Db,
    user_id: i64,
    flashcard_id: i64,
    label: &str,
    grade: Grade,
    today: NaiveDate,
) -> Result<Outcome> {
    let existing = find_state(db, user_id, flashcard_id, label).await?;
    let is_new = existing.is_none();
    let mut state = existing.unwrap_or_else(|| CardState {
        user_id,
        flashcard_id,
        label: label.to_owned(),
        r#box: leitner::MIN_BOX,
        introduced_on: today,
        ..Default::default()
    });
    let outcome = leitner::review(state.r#box, today, grade);
    state.r#box = outcome.box_after;
    state.due_on = outcome.due_on;
    state.reviews += 1;
    if grade == Grade::Again {
        state.lapses += 1;
    }
    state.last_grade = Some(grade.as_str().to_owned());
    if is_new {
        CardState::create(db, state).await?;
    } else {
        state.save(db).await?;
    }
    CardReview::create(
        db,
        CardReview {
            user_id,
            flashcard_id,
            label: label.to_owned(),
            grade: grade.as_str().to_owned(),
            reviewed_at: renox::db::now(),
            box_before: outcome.box_before,
            box_after: outcome.box_after,
            ..Default::default()
        },
    )
    .await?;
    Ok(outcome)
}
