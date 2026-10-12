//! The Leitner boxes of the Error Log (the same rules as the flashcards).
//!
//! Box 1 = every day, 2 = every 2 days, 3 = every 4 days, 4 = every 7 days, 5 = every 14 days.
//! `again` goes back to box 1, `hard` stays, `good` moves up one, `easy` two (at most 5).
//! An entry in box 5 that is answered `good` (or `easy`) again is resolved.

use renox::chrono::{Duration, NaiveDate};

pub const MAX_BOX: i64 = 5;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Grade {
    Again,
    Hard,
    Good,
    Easy,
}

impl Grade {
    pub fn parse(s: &str) -> Option<Grade> {
        match s {
            "again" => Some(Grade::Again),
            "hard" => Some(Grade::Hard),
            "good" => Some(Grade::Good),
            "easy" => Some(Grade::Easy),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Grade::Again => "again",
            Grade::Hard => "hard",
            Grade::Good => "good",
            Grade::Easy => "easy",
        }
    }
}

/// Days until the next review of an entry in `box_no` (clamped to 1..=5).
pub fn interval_days(box_no: i64) -> i64 {
    match box_no.clamp(1, MAX_BOX) {
        1 => 1,
        2 => 2,
        3 => 4,
        4 => 7,
        _ => 14,
    }
}

pub fn due_on(today: NaiveDate, box_no: i64) -> NaiveDate {
    today + Duration::days(interval_days(box_no))
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Next {
    pub box_no: i64,
    pub resolved: bool,
}

/// The box after a review, and whether the entry is now resolved.
pub fn apply(box_no: i64, grade: Grade) -> Next {
    let box_no = box_no.clamp(1, MAX_BOX);
    let resolved = box_no == MAX_BOX && matches!(grade, Grade::Good | Grade::Easy);
    let next = match grade {
        Grade::Again => 1,
        Grade::Hard => box_no,
        Grade::Good => (box_no + 1).min(MAX_BOX),
        Grade::Easy => (box_no + 2).min(MAX_BOX),
    };
    Next {
        box_no: next,
        resolved,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn intervals_follow_the_boxes() {
        let days: Vec<i64> = (1..=5).map(interval_days).collect();
        assert_eq!(days, vec![1, 2, 4, 7, 14]);
        assert_eq!(interval_days(0), 1);
        assert_eq!(interval_days(9), 14);
    }

    #[test]
    fn grades_move_the_box() {
        assert_eq!(apply(3, Grade::Again).box_no, 1);
        assert_eq!(apply(3, Grade::Hard).box_no, 3);
        assert_eq!(apply(3, Grade::Good).box_no, 4);
        assert_eq!(apply(3, Grade::Easy).box_no, 5);
        assert_eq!(apply(4, Grade::Easy).box_no, 5);
        assert_eq!(apply(1, Grade::Easy).box_no, 3);
        assert!(!apply(3, Grade::Easy).resolved);
        assert!(!apply(4, Grade::Good).resolved);
    }

    #[test]
    fn box_five_then_good_resolves() {
        assert_eq!(
            apply(5, Grade::Good),
            Next {
                box_no: 5,
                resolved: true
            }
        );
        assert!(apply(5, Grade::Easy).resolved);
        assert!(!apply(5, Grade::Hard).resolved);
        let again = apply(5, Grade::Again);
        assert_eq!((again.box_no, again.resolved), (1, false));
    }

    #[test]
    fn due_date_adds_the_interval() {
        let d = NaiveDate::from_ymd_opt(2026, 10, 12).unwrap();
        assert_eq!(due_on(d, 1), NaiveDate::from_ymd_opt(2026, 10, 13).unwrap());
        assert_eq!(due_on(d, 5), NaiveDate::from_ymd_opt(2026, 10, 26).unwrap());
    }

    #[test]
    fn grades_parse() {
        assert_eq!(Grade::parse("good"), Some(Grade::Good));
        assert_eq!(Grade::parse("nope"), None);
        assert_eq!(Grade::Easy.as_str(), "easy");
    }
}
