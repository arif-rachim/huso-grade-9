//! Mastery of a subtopic (0-100), the number behind the colours of the syllabus map.
//!
//! `round(100 * (0.6 * question accuracy over the last 14 days + 0.4 * share of cards in box >= 3))`.
//! A correct-but-guessed answer counts as half correct. With fewer than 3 answers and no reviewed
//! cards a subtopic is "not started". With no cards at all the questions weigh 100 % (and the
//! other way round). [`mastery`] is a pure function; [`load`] gathers its inputs for all subtopics
//! in a constant number of queries.

use renox::chrono::Duration;
use renox::prelude::*;
use std::collections::HashMap;

/// How many days of answers count.
pub const WINDOW_DAYS: i64 = 14;
/// Fewer answers than this, and no reviewed card, means "not started".
pub const MIN_ANSWERS: i64 = 3;
/// Leitner box from which a card counts as known.
pub const KNOWN_BOX: i64 = 3;

/// What the student has done on one subtopic.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Evidence {
    /// Answers given in the window (blank answers are not counted).
    pub answers: i64,
    /// Correct answers that were not guessed.
    pub correct: i64,
    /// Correct answers marked as a guess (worth half).
    pub guessed_correct: i64,
    /// Cards of the subtopic.
    pub cards: i64,
    /// Cards the student has reviewed at least once.
    pub reviewed: i64,
    /// Cards in box 3 or higher.
    pub known: i64,
}

impl Evidence {
    /// Question points in halves: a clean correct answer is 2, a guessed one 1.
    pub fn half_points(&self) -> i64 {
        2 * self.correct + self.guessed_correct
    }

    /// Question accuracy as a percentage, if there are answers.
    pub fn accuracy_percent(&self) -> Option<i64> {
        (self.answers > 0).then(|| (50 * self.half_points() + self.answers / 2) / self.answers)
    }
}

/// The mastery of a subtopic, or `None` for "not started".
pub fn mastery(e: &Evidence) -> Option<i32> {
    if e.answers < MIN_ANSWERS && e.reviewed == 0 {
        return None;
    }
    let (n, t, p, h) = (e.answers, e.cards, e.half_points(), e.known);
    // Integer arithmetic, rounded half up: accuracy = p / 2n, share = h / t.
    let (num, den) = match (n > 0, t > 0) {
        (true, true) => (30 * p * t + 40 * h * n, n * t),
        (true, false) => (50 * p, n),
        (false, true) => (100 * h, t),
        (false, false) => return None,
    };
    Some(((2 * num + den) / (2 * den)).clamp(0, 100) as i32)
}

/// The colour band of a mastery value.
pub fn band(value: Option<i32>) -> &'static str {
    match value {
        None => "grey",
        Some(v) if v < 40 => "red",
        Some(v) if v < 70 => "yellow",
        Some(_) => "green",
    }
}

/// The evidence of every subtopic, by topic id. Two queries, however many subtopics there are.
pub async fn load(db: &Db, user_id: i64) -> Result<HashMap<i64, Evidence>> {
    let today = crate::clock::today();
    let since = (today - Duration::days(WINDOW_DAYS)).to_string();
    let mut out: HashMap<i64, Evidence> = HashMap::new();

    let answers: Vec<(i64, i64, i64, i64)> = renox::db::sql(
        "SELECT q.topic_id, COUNT(*), \
                COALESCE(SUM(CASE WHEN a.is_correct = 1 AND a.guessed = 0 THEN 1 ELSE 0 END), 0), \
                COALESCE(SUM(CASE WHEN a.is_correct = 1 AND a.guessed = 1 THEN 1 ELSE 0 END), 0) \
         FROM answers a \
         JOIN attempts t ON t.id = a.attempt_id \
         JOIN questions q ON q.id = a.question_id \
         WHERE t.user_id = ? AND a.choice IS NOT NULL AND a.answered_at >= ? \
         GROUP BY q.topic_id",
    )
    .bind(user_id)
    .bind(since)
    .fetch_as(db)
    .await?;
    for (topic, n, correct, guessed) in answers {
        let e = out.entry(topic).or_default();
        e.answers = n;
        e.correct = correct;
        e.guessed_correct = guessed;
    }

    // A card counts by its weakest part: an occlusion card has one state per hidden label.
    let cards: Vec<(i64, i64, i64, i64)> = renox::db::sql(
        "SELECT f.topic_id, COUNT(*), \
                COALESCE(SUM(CASE WHEN m.min_box IS NOT NULL THEN 1 ELSE 0 END), 0), \
                COALESCE(SUM(CASE WHEN m.min_box >= ? THEN 1 ELSE 0 END), 0) \
         FROM flashcards f \
         LEFT JOIN (SELECT flashcard_id, MIN(box) AS min_box FROM card_states \
                    WHERE user_id = ? GROUP BY flashcard_id) m ON m.flashcard_id = f.id \
         WHERE f.archived_at IS NULL \
         GROUP BY f.topic_id",
    )
    .bind(KNOWN_BOX)
    .bind(user_id)
    .fetch_as(db)
    .await?;
    for (topic, total, reviewed, known) in cards {
        let e = out.entry(topic).or_default();
        e.cards = total;
        e.reviewed = reviewed;
        e.known = known;
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ev(a: i64, c: i64, g: i64, cards: i64, rev: i64, known: i64) -> Evidence {
        Evidence {
            answers: a,
            correct: c,
            guessed_correct: g,
            cards,
            reviewed: rev,
            known,
        }
    }

    #[test]
    fn the_issue_example_gives_71() {
        // 10 answers: 8 correct, 1 correct-but-guessed, 1 wrong; 4 cards, 2 in box 3+.
        // accuracy 8.5/10 = 0.85; share 0.5 -> 100 * (0.51 + 0.2) = 71
        assert_eq!(mastery(&ev(10, 8, 1, 4, 4, 2)), Some(71));
        assert_eq!(ev(10, 8, 1, 4, 4, 2).accuracy_percent(), Some(85));
    }

    #[test]
    fn nothing_or_too_little_is_not_started() {
        assert_eq!(mastery(&Evidence::default()), None);
        assert_eq!(mastery(&ev(2, 2, 0, 5, 0, 0)), None);
    }

    #[test]
    fn two_answers_and_one_reviewed_card_start_it() {
        assert_eq!(mastery(&ev(2, 2, 0, 4, 1, 0)), Some(60));
    }

    #[test]
    fn no_cards_means_questions_only() {
        assert_eq!(mastery(&ev(4, 3, 0, 0, 0, 0)), Some(75));
        assert_eq!(mastery(&ev(4, 0, 4, 0, 0, 0)), Some(50)); // all guessed: half
    }

    #[test]
    fn no_answers_means_cards_only() {
        assert_eq!(mastery(&ev(0, 0, 0, 4, 3, 3)), Some(75));
        // one answer still counts: (30*2*4 + 40*3*1) / 4 = 90
        assert_eq!(mastery(&ev(1, 1, 0, 4, 3, 3)), Some(90));
    }

    #[test]
    fn unreviewed_cards_pull_the_value_down() {
        assert_eq!(mastery(&ev(5, 5, 0, 10, 0, 0)), Some(60));
        assert_eq!(mastery(&ev(5, 5, 0, 10, 10, 10)), Some(100));
    }

    #[test]
    fn colours() {
        assert_eq!(band(None), "grey");
        assert_eq!(band(Some(0)), "red");
        assert_eq!(band(Some(39)), "red");
        assert_eq!(band(Some(40)), "yellow");
        assert_eq!(band(Some(69)), "yellow");
        assert_eq!(band(Some(70)), "green");
        assert_eq!(band(Some(100)), "green");
    }
}
