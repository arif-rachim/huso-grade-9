//! The 5-box Leitner system, as pure functions (docs/PROJECT.md "Leitner boxes").
//!
//! Box 1 is reviewed every day, box 2 every 2 days, 3 every 4, 4 every 7 and 5 every 14.
//! A new card starts in box 1, due today. `again` goes back to box 1, `hard` stays,
//! `good` moves up one box, `easy` moves up two (never past box 5).

use renox::chrono::{Duration, NaiveDate};

pub const MIN_BOX: i64 = 1;
pub const MAX_BOX: i64 = 5;
/// At most this many cards the student has never seen are introduced per day.
pub const NEW_CARDS_PER_DAY: i64 = 20;

/// Days between reviews, by box (index 0 is box 1).
const INTERVALS: [i64; 5] = [1, 2, 4, 7, 14];

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Grade {
    Again,
    Hard,
    Good,
    Easy,
}

impl Grade {
    pub const ALL: [Grade; 4] = [Grade::Again, Grade::Hard, Grade::Good, Grade::Easy];

    /// The word stored in `card_reviews.grade`.
    pub fn as_str(self) -> &'static str {
        match self {
            Grade::Again => "again",
            Grade::Hard => "hard",
            Grade::Good => "good",
            Grade::Easy => "easy",
        }
    }

    pub fn parse(text: &str) -> Option<Grade> {
        Grade::ALL.into_iter().find(|g| g.as_str() == text)
    }

    /// The keyboard number: 1 Again, 2 Hard, 3 Good, 4 Easy.
    pub fn from_number(n: i64) -> Option<Grade> {
        usize::try_from(n - 1)
            .ok()
            .and_then(|i| Grade::ALL.get(i).copied())
    }

    pub fn number(self) -> i64 {
        Grade::ALL.iter().position(|g| *g == self).unwrap_or(0) as i64 + 1
    }

    pub fn label(self) -> &'static str {
        match self {
            Grade::Again => "Again",
            Grade::Hard => "Hard",
            Grade::Good => "Good",
            Grade::Easy => "Easy",
        }
    }
}

/// Keeps a box number inside 1..=5.
pub fn clamp_box(box_: i64) -> i64 {
    box_.clamp(MIN_BOX, MAX_BOX)
}

/// Days until the next review for a card in `box_`.
pub fn interval_days(box_: i64) -> i64 {
    INTERVALS[(clamp_box(box_) - 1) as usize]
}

/// The box a card in `box_` moves to after `grade`.
pub fn next_box(box_: i64, grade: Grade) -> i64 {
    let box_ = clamp_box(box_);
    match grade {
        Grade::Again => MIN_BOX,
        Grade::Hard => box_,
        Grade::Good => clamp_box(box_ + 1),
        Grade::Easy => clamp_box(box_ + 2),
    }
}

/// The day a card in `box_` is due again when reviewed on `today`.
pub fn due_on(today: NaiveDate, box_: i64) -> NaiveDate {
    today + Duration::days(interval_days(box_))
}

/// What reviewing a card does to it.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Outcome {
    pub box_before: i64,
    pub box_after: i64,
    pub due_on: NaiveDate,
}

pub fn review(box_: i64, today: NaiveDate, grade: Grade) -> Outcome {
    let box_after = next_box(box_, grade);
    Outcome {
        box_before: clamp_box(box_),
        box_after,
        due_on: due_on(today, box_after),
    }
}

/// "tomorrow", "2 days", ... for the button under a grade.
pub fn interval_label(days: i64) -> String {
    match days {
        d if d <= 0 => "today".to_owned(),
        1 => "tomorrow".to_owned(),
        d => format!("{d} days"),
    }
}

/// How long until the card comes back if it is graded `grade` while in `box_`.
pub fn preview(box_: i64, grade: Grade) -> String {
    interval_label(interval_days(next_box(box_, grade)))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(y: i32, m: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(y, m, day).unwrap()
    }

    #[test]
    fn intervals_are_1_2_4_7_14_days() {
        let days: Vec<i64> = (1..=5).map(interval_days).collect();
        assert_eq!(days, [1, 2, 4, 7, 14]);
    }

    #[test]
    fn intervals_clamp_out_of_range_boxes() {
        assert_eq!(interval_days(0), 1);
        assert_eq!(interval_days(-3), 1);
        assert_eq!(interval_days(6), 14);
        assert_eq!(interval_days(99), 14);
    }

    #[test]
    fn again_always_goes_back_to_box_1() {
        for b in 1..=5 {
            assert_eq!(next_box(b, Grade::Again), 1, "box {b}");
        }
    }

    #[test]
    fn hard_stays_in_the_same_box() {
        for b in 1..=5 {
            assert_eq!(next_box(b, Grade::Hard), b, "box {b}");
        }
    }

    #[test]
    fn good_moves_up_one_and_stops_at_5() {
        let got: Vec<i64> = (1..=5).map(|b| next_box(b, Grade::Good)).collect();
        assert_eq!(got, [2, 3, 4, 5, 5]);
    }

    #[test]
    fn easy_moves_up_two_and_stops_at_5() {
        let got: Vec<i64> = (1..=5).map(|b| next_box(b, Grade::Easy)).collect();
        assert_eq!(got, [3, 4, 5, 5, 5]);
    }

    #[test]
    fn every_grade_and_box_stays_inside_1_to_5() {
        for b in -2..=8 {
            for g in Grade::ALL {
                let n = next_box(b, g);
                assert!((1..=5).contains(&n), "box {b} {g:?} -> {n}");
            }
        }
    }

    #[test]
    fn a_new_card_graded_good_is_due_in_two_days() {
        // Box 1 -> 2, so due_on = today + 2 (that is, tomorrow + 1).
        let out = review(1, d(2026, 10, 12), Grade::Good);
        assert_eq!(out.box_before, 1);
        assert_eq!(out.box_after, 2);
        assert_eq!(out.due_on, d(2026, 10, 14));
    }

    #[test]
    fn again_makes_the_card_due_tomorrow() {
        let out = review(4, d(2026, 10, 12), Grade::Again);
        assert_eq!(out.box_after, 1);
        assert_eq!(out.due_on, d(2026, 10, 13));
    }

    #[test]
    fn hard_in_box_5_is_due_in_14_days() {
        let out = review(5, d(2026, 10, 12), Grade::Hard);
        assert_eq!(out.box_after, 5);
        assert_eq!(out.due_on, d(2026, 10, 26));
    }

    #[test]
    fn easy_from_box_3_lands_in_box_5() {
        let out = review(3, d(2026, 10, 31), Grade::Easy);
        assert_eq!(out.box_after, 5);
        assert_eq!(out.due_on, d(2026, 11, 14));
    }

    #[test]
    fn grades_round_trip_through_words_and_numbers() {
        for g in Grade::ALL {
            assert_eq!(Grade::parse(g.as_str()), Some(g));
            assert_eq!(Grade::from_number(g.number()), Some(g));
        }
        assert_eq!(Grade::from_number(0), None);
        assert_eq!(Grade::from_number(5), None);
        assert_eq!(Grade::from_number(-1), None);
        assert_eq!(Grade::parse("great"), None);
        assert_eq!(Grade::Again.number(), 1);
        assert_eq!(Grade::Easy.number(), 4);
    }

    #[test]
    fn button_labels_say_tomorrow_or_days() {
        assert_eq!(interval_label(1), "tomorrow");
        assert_eq!(interval_label(4), "4 days");
        assert_eq!(interval_label(0), "today");
        assert_eq!(preview(1, Grade::Again), "tomorrow");
        assert_eq!(preview(1, Grade::Good), "2 days");
        assert_eq!(preview(2, Grade::Good), "4 days");
        assert_eq!(preview(3, Grade::Easy), "14 days");
    }
}
