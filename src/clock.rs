//! "Today" in the family's time zone (Asia/Jakarta, UTC+7, no daylight saving) and the
//! countdown to the exam. Time is always read through `renox::db::now()` so tests can travel.

use renox::chrono::{Duration, NaiveDate};

/// Round 1 of HUSO, Sunday 15 Nov 2026.
pub const EXAM_DATE: (i32, u32, u32) = (2026, 11, 15);

/// Jakarta is a fixed UTC+7.
const JAKARTA_HOURS: i64 = 7;

pub fn exam_date() -> NaiveDate {
    NaiveDate::from_ymd_opt(EXAM_DATE.0, EXAM_DATE.1, EXAM_DATE.2).expect("valid exam date")
}

/// The Jakarta calendar date right now.
pub fn today() -> NaiveDate {
    (renox::db::now() + Duration::hours(JAKARTA_HOURS)).date_naive()
}

/// "D-N to HUSO", "HUSO day!", or nothing once the exam is over.
pub fn countdown_label(today: NaiveDate) -> Option<String> {
    let days = (exam_date() - today).num_days();
    match days {
        d if d > 0 => Some(format!("D-{d} to HUSO")),
        0 => Some("HUSO day!".to_owned()),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(y: i32, m: u32, day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(y, m, day).unwrap()
    }

    #[test]
    fn counts_down_to_the_exam() {
        assert_eq!(
            countdown_label(d(2026, 11, 14)).as_deref(),
            Some("D-1 to HUSO")
        );
        assert_eq!(
            countdown_label(d(2026, 10, 12)).as_deref(),
            Some("D-34 to HUSO")
        );
    }

    #[test]
    fn says_huso_day_on_the_day_and_hides_after() {
        assert_eq!(
            countdown_label(d(2026, 11, 15)).as_deref(),
            Some("HUSO day!")
        );
        assert_eq!(countdown_label(d(2026, 11, 16)), None);
    }
}
