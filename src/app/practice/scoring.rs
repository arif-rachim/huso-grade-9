//! HUSO scoring as pure functions (no database, no clock).
//!
//! Every question is worth +1 when right, -0.25 when wrong and 0 when blank. We store
//! **quarter points** as integers: `raw_q = 4 * correct - wrong`, shown as `raw_q / 4`
//! with two decimals. Percents are kept as **basis points** (1/100 of a percent) so that no
//! float is needed: 72.5 % is `7250`.

/// Correct, wrong and blank answers of one subject (or one section).
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct Tally {
    pub correct: i64,
    pub wrong: i64,
    pub blank: i64,
}

impl Tally {
    pub fn total(&self) -> i64 {
        self.correct + self.wrong + self.blank
    }

    /// Quarter points.
    pub fn raw_q(&self) -> i64 {
        raw_q(self.correct, self.wrong)
    }

    /// Percent correct (of all questions, blanks included) in basis points.
    pub fn percent_bp(&self) -> i64 {
        percent_bp(self.correct, self.total())
    }
}

/// `4 * correct - wrong`: the raw score in quarter points.
pub fn raw_q(correct: i64, wrong: i64) -> i64 {
    4 * correct - wrong
}

/// Quarter points as text with two decimals: `36` -> `"9.00"`, `-1` -> `"-0.25"`.
pub fn format_quarters(raw_q: i64) -> String {
    let sign = if raw_q < 0 { "-" } else { "" };
    let abs = raw_q.abs();
    format!("{sign}{}.{:02}", abs / 4, (abs % 4) * 25)
}

/// Percent correct in basis points, rounded to the nearest; 0 when there are no questions.
pub fn percent_bp(correct: i64, total: i64) -> i64 {
    if total <= 0 {
        return 0;
    }
    (correct * 10_000 * 2 + total) / (total * 2)
}

/// Basis points as text with one decimal: `7250` -> `"72.5"`, `10000` -> `"100.0"`.
pub fn format_percent(bp: i64) -> String {
    let tenths = (bp + 5) / 10;
    format!("{}.{}", tenths / 10, tenths % 10)
}

/// A subject's result in a simulation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SubjectScore {
    pub slug: String,
    pub tally: Tally,
}

/// The "total of the best four subjects by percent".
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BestFour {
    /// Indexes (into the input) of the subjects that count, best first.
    pub kept: Vec<usize>,
    /// The subject left out (none when there are four subjects or fewer).
    pub dropped: Option<usize>,
    /// Sum of the kept percents, in basis points (at most 40 000).
    pub total_bp: i64,
}

/// Keep the four best subjects by percent. A tie goes to the higher raw score, then to the
/// subject that comes first, so the answer never changes between runs.
pub fn best_four(scores: &[SubjectScore]) -> BestFour {
    let mut order: Vec<usize> = (0..scores.len()).collect();
    order.sort_by(|&a, &b| {
        let (x, y) = (&scores[a].tally, &scores[b].tally);
        y.percent_bp()
            .cmp(&x.percent_bp())
            .then(y.raw_q().cmp(&x.raw_q()))
            .then(a.cmp(&b))
    });
    let dropped = if order.len() > 4 { order.pop() } else { None };
    order.truncate(4);
    let total_bp: i64 = order.iter().map(|&i| scores[i].tally.percent_bp()).sum();
    BestFour {
        kept: order,
        dropped,
        total_bp: total_bp.min(40_000),
    }
}

/// Should an answer land in the Error Log? It was wrong (a blank counts as not right) or the
/// student marked it as a guess, even if the guess was lucky.
pub fn is_wrong_or_guessed(is_correct: bool, guessed: bool) -> bool {
    !is_correct || guessed
}

#[cfg(test)]
mod tests {
    use super::*;

    fn score(slug: &str, correct: i64, wrong: i64, blank: i64) -> SubjectScore {
        SubjectScore {
            slug: slug.into(),
            tally: Tally {
                correct,
                wrong,
                blank,
            },
        }
    }

    #[test]
    fn ten_right_four_wrong_one_blank_is_nine_points() {
        let t = Tally {
            correct: 10,
            wrong: 4,
            blank: 1,
        };
        assert_eq!(t.raw_q(), 36);
        assert_eq!(format_quarters(t.raw_q()), "9.00");
        assert_eq!(t.total(), 15);
        assert_eq!(format_percent(t.percent_bp()), "66.7");
    }

    #[test]
    fn quarter_points_show_two_decimals() {
        assert_eq!(format_quarters(0), "0.00");
        assert_eq!(format_quarters(1), "0.25");
        assert_eq!(format_quarters(3), "0.75");
        assert_eq!(format_quarters(-1), "-0.25");
        assert_eq!(format_quarters(-6), "-1.50");
        assert_eq!(format_quarters(37), "9.25");
    }

    #[test]
    fn percent_handles_empty_and_rounding() {
        assert_eq!(percent_bp(0, 0), 0);
        assert_eq!(percent_bp(1, 3), 3333);
        assert_eq!(percent_bp(2, 3), 6667);
        assert_eq!(percent_bp(5, 5), 10_000);
        assert_eq!(format_percent(10_000), "100.0");
        assert_eq!(format_percent(0), "0.0");
        assert_eq!(format_percent(7250), "72.5");
    }

    #[test]
    fn best_four_drops_the_lowest_percent() {
        let scores = [
            score("math", 6, 2, 4),        // 50.0
            score("physics", 15, 3, 2),    // 75.0
            score("chemistry", 14, 7, 14), // 40.0
            score("biology", 30, 5, 5),    // 75.0
            score("earth", 36, 4, 5),      // 80.0
        ];
        let best = best_four(&scores);
        assert_eq!(best.dropped, Some(2), "chemistry has the lowest percent");
        assert_eq!(
            best.kept,
            vec![4, 3, 1, 0],
            "75 % tie: biology has the higher raw score"
        );
        assert_eq!(best.total_bp, 8000 + 7500 + 7500 + 5000);
    }

    #[test]
    fn best_four_breaks_ties_by_raw_score_then_order() {
        // Same 50 %: physics has the better raw score (fewer wrong), so math is dropped.
        let scores = [
            score("math", 5, 5, 0),
            score("physics", 5, 0, 5),
            score("chemistry", 9, 1, 0),
            score("biology", 9, 1, 0),
            score("earth", 9, 1, 0),
        ];
        let best = best_four(&scores);
        assert_eq!(best.dropped, Some(0));
        // Fully equal subjects: the last one is dropped.
        let equal = [
            score("a", 1, 0, 1),
            score("b", 1, 0, 1),
            score("c", 1, 0, 1),
            score("d", 1, 0, 1),
            score("e", 1, 0, 1),
        ];
        assert_eq!(best_four(&equal).dropped, Some(4));
    }

    #[test]
    fn four_subjects_or_fewer_drop_nothing() {
        let scores = [score("math", 1, 0, 0), score("physics", 0, 1, 0)];
        let best = best_four(&scores);
        assert_eq!(best.dropped, None);
        assert_eq!(best.kept, vec![0, 1]);
        assert_eq!(best.total_bp, 10_000);
        assert_eq!(best_four(&[]).total_bp, 0);
    }

    #[test]
    fn wrong_blank_or_guessed_answers_go_to_the_error_log() {
        assert!(is_wrong_or_guessed(false, false));
        assert!(is_wrong_or_guessed(true, true));
        assert!(is_wrong_or_guessed(false, true));
        assert!(!is_wrong_or_guessed(true, false));
    }
}
