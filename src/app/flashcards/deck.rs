//! What the student has to review, worked out in memory from the cards and their states:
//! the review queue, the per-subject numbers for the overview, and the due count for Today.

use super::card::OCCLUSION;
use super::leitner::{MAX_BOX, NEW_CARDS_PER_DAY};
use super::models::CardState;
use super::svg;
use crate::app::content::models::{Flashcard, PlanDay, Subject, Topic};
use renox::chrono::NaiveDate;
use renox::prelude::*;
use serde::Serialize;
use std::collections::{HashMap, HashSet};
use std::path::PathBuf;

/// One thing to review: a card, or one hidden label of an occlusion card.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, serde::Deserialize)]
pub struct Unit {
    /// `flashcards.id`
    pub c: i64,
    /// The hidden label of an occlusion card, else empty.
    pub l: String,
}

#[derive(Debug, Default)]
pub struct Queue {
    pub items: Vec<Unit>,
    /// How many of `items` are due again (the rest are new cards).
    pub due: usize,
    pub new: usize,
}

#[derive(Debug, Clone, Serialize)]
pub struct SubjectStats {
    pub slug: String,
    pub name: String,
    pub color: String,
    pub emoji: String,
    pub total: i64,
    pub new: i64,
    pub due: i64,
    /// Cards in boxes 1 to 5.
    pub boxes: [i64; 5],
}

pub struct Deck {
    pub subjects: Vec<Subject>,
    topics: HashMap<i64, Topic>,
    pub cards: Vec<Flashcard>,
    pub states: Vec<CardState>,
    public_dir: PathBuf,
}

pub fn public_dir() -> PathBuf {
    crate::app::content::project_dir().join("public")
}

impl Deck {
    pub async fn load(db: &Db, user_id: i64) -> Result<Deck> {
        let subjects = Subject::query().order_by(Subject::POSITION).get(db).await?;
        let topics = Topic::query()
            .get(db)
            .await?
            .into_iter()
            .map(|t| (t.id, t))
            .collect();
        let cards = Flashcard::query()
            .where_(Flashcard::ARCHIVED_AT.is_null())
            .order_by(Flashcard::ID)
            .get(db)
            .await?;
        let states = CardState::query()
            .where_(CardState::USER_ID.eq(user_id))
            .get(db)
            .await?;
        Ok(Deck {
            subjects,
            topics,
            cards,
            states,
            public_dir: public_dir(),
        })
    }

    /// The reviews a card gives: one per hidden label for an occlusion card, else one.
    pub fn labels(&self, card: &Flashcard) -> Vec<String> {
        if card.card_type == OCCLUSION
            && let Some(visual) = card.visual.as_deref()
            && let Some(picture) = svg::read(&self.public_dir, visual)
        {
            let labels = svg::labels(&picture);
            if !labels.is_empty() {
                return labels;
            }
        }
        vec![String::new()]
    }

    pub fn subject_of(&self, card: &Flashcard) -> Option<&Subject> {
        let topic = self.topics.get(&card.topic_id)?;
        self.subjects.iter().find(|s| s.id == topic.subject_id)
    }

    fn topic_position(&self, card: &Flashcard) -> i64 {
        self.topics.get(&card.topic_id).map_or(0, |t| t.position)
    }

    /// Cards that are due today, then new cards (at most the day's allowance left), today's
    /// subject first.
    /// `only` limits the queue to one subject (the overview's filter).
    pub fn queue(&self, today: NaiveDate, plan_subject: Option<&str>, only: Option<&str>) -> Queue {
        let in_scope = |card: &Flashcard| {
            only.is_none_or(|slug| self.subject_of(card).is_some_and(|s| s.slug == slug))
        };
        let active: HashSet<i64> = self
            .cards
            .iter()
            .filter(|c| in_scope(c))
            .map(|c| c.id)
            .collect();

        let mut due: Vec<&CardState> = self
            .states
            .iter()
            .filter(|s| s.due_on <= today && active.contains(&s.flashcard_id))
            .collect();
        due.sort_by_key(|s| (s.due_on, s.r#box, s.flashcard_id, s.label.clone()));

        let introduced_today = self
            .states
            .iter()
            .filter(|s| s.introduced_on == today)
            .count() as i64;
        let mut room = (NEW_CARDS_PER_DAY - introduced_today).max(0) as usize;

        let seen: HashSet<(i64, &str)> = self
            .states
            .iter()
            .map(|s| (s.flashcard_id, s.label.as_str()))
            .collect();
        let mut candidates: Vec<&Flashcard> = self.cards.iter().filter(|c| in_scope(c)).collect();
        candidates.sort_by_key(|c| {
            let subject = self.subject_of(c);
            let first = plan_subject.is_some_and(|p| subject.is_some_and(|s| s.slug == p));
            (
                !first,
                subject.map_or(i64::MAX, |s| s.position),
                self.topic_position(c),
                c.id,
            )
        });
        let mut new_units = Vec::new();
        for card in candidates {
            if room == 0 {
                break;
            }
            for label in self.labels(card) {
                if room > 0 && !seen.contains(&(card.id, label.as_str())) {
                    new_units.push(Unit { c: card.id, l: label });
                    room -= 1;
                }
            }
        }

        let mut items: Vec<Unit> = due
            .iter()
            .map(|s| Unit {
                c: s.flashcard_id,
                l: s.label.clone(),
            })
            .collect();
        let (due_n, new_n) = (items.len(), new_units.len());
        items.extend(new_units);
        Queue {
            items,
            due: due_n,
            new: new_n,
        }
    }

    pub fn stats(&self, today: NaiveDate) -> Vec<SubjectStats> {
        let mut out: Vec<SubjectStats> = self
            .subjects
            .iter()
            .map(|s| SubjectStats {
                slug: s.slug.clone(),
                name: s.name.clone(),
                color: s.color.clone(),
                emoji: s.emoji.clone(),
                total: 0,
                new: 0,
                due: 0,
                boxes: [0; 5],
            })
            .collect();
        let index_of = |card: &Flashcard| {
            self.subject_of(card)
                .and_then(|s| self.subjects.iter().position(|x| x.id == s.id))
        };
        let mut by_card: HashMap<i64, usize> = HashMap::new();
        for card in &self.cards {
            let Some(i) = index_of(card) else { continue };
            by_card.insert(card.id, i);
            out[i].total += self.labels(card).len() as i64;
        }
        let mut started = vec![0i64; out.len()];
        for state in &self.states {
            let Some(&i) = by_card.get(&state.flashcard_id) else {
                continue;
            };
            started[i] += 1;
            out[i].boxes[(state.r#box.clamp(1, MAX_BOX) - 1) as usize] += 1;
            if state.due_on <= today {
                out[i].due += 1;
            }
        }
        for (i, s) in out.iter_mut().enumerate() {
            s.new = (s.total - started[i]).max(0);
        }
        out
    }
}

/// The subject the plan names for `today` (`math`, `physics`, ...), if it names one.
pub async fn plan_subject(db: &Db, today: NaiveDate) -> Result<Option<String>> {
    Ok(PlanDay::query()
        .where_(PlanDay::DATE.eq(today))
        .first(db)
        .await?
        .map(|d| d.subject))
}

/// The student's review queue for today.
pub async fn queue_for(
    db: &Db,
    user_id: i64,
    today: NaiveDate,
    only: Option<&str>,
) -> Result<Queue> {
    let deck = Deck::load(db, user_id).await?;
    let subject = plan_subject(db, today).await?;
    Ok(deck.queue(today, subject.as_deref(), only))
}

/// How many cards the student can review today: what is due again, plus the new cards
/// still allowed today (at most 20 a day). The Today page shows this number.
pub async fn due_count(db: &Db, user_id: i64, today: NaiveDate) -> Result<i64> {
    Ok(queue_for(db, user_id, today, None).await?.items.len() as i64)
}

/// The id of the student's account: the user themselves, or for the parent the user who
/// has the `student` role.
pub async fn student_id(db: &Db, user: &AuthUser) -> Result<Option<i64>> {
    if user.has_role(crate::app::accounts::STUDENT) {
        return Ok(Some(user.id));
    }
    let id: Option<i64> = renox::db::sql(
        "SELECT ru.user_id FROM role_user ru JOIN roles r ON r.id = ru.role_id \
         WHERE r.name = ? ORDER BY ru.user_id LIMIT 1",
    )
    .bind(crate::app::accounts::STUDENT)
    .scalar(db)
    .await
    .ok();
    Ok(id)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn d(day: u32) -> NaiveDate {
        NaiveDate::from_ymd_opt(2026, 10, day).unwrap()
    }

    fn subject(id: i64, slug: &str, position: i64) -> Subject {
        Subject {
            id,
            slug: slug.into(),
            name: slug.into(),
            color: "#000000".into(),
            position,
            ..Default::default()
        }
    }

    fn topic(id: i64, subject_id: i64) -> Topic {
        Topic {
            id,
            subject_id,
            position: id,
            ..Default::default()
        }
    }

    fn card(id: i64, topic_id: i64) -> Flashcard {
        Flashcard {
            id,
            topic_id,
            card_type: "basic".into(),
            ..Default::default()
        }
    }

    fn state(card: i64, due: NaiveDate, introduced: NaiveDate) -> CardState {
        CardState {
            flashcard_id: card,
            r#box: 2,
            due_on: due,
            introduced_on: introduced,
            ..Default::default()
        }
    }

    fn deck(cards: Vec<Flashcard>, states: Vec<CardState>) -> Deck {
        Deck {
            subjects: vec![subject(1, "math", 0), subject(2, "biology", 1)],
            topics: [(10, topic(10, 1)), (20, topic(20, 2))].into_iter().collect(),
            cards,
            states,
            public_dir: PathBuf::from("/nonexistent"),
        }
    }

    #[test]
    fn at_most_20_new_cards_and_todays_subject_first() {
        let mut cards: Vec<Flashcard> = (1..=15).map(|i| card(i, 10)).collect(); // math
        cards.extend((101..=115).map(|i| card(i, 20))); // biology
        let deck = deck(cards, vec![]);

        let q = deck.queue(d(12), Some("biology"), None);
        assert_eq!(q.items.len(), 20);
        assert_eq!((q.due, q.new), (0, 20));
        let ids: Vec<i64> = q.items.iter().map(|u| u.c).collect();
        assert_eq!(&ids[..15], &(101..=115).collect::<Vec<_>>()[..], "biology first");
        assert_eq!(&ids[15..], &[1, 2, 3, 4, 5], "then the other subjects");

        let q = deck.queue(d(12), Some("math"), None);
        assert_eq!(q.items[0].c, 1);
        assert_eq!(q.items[15].c, 101);

        // Not a subject (e.g. a review day): the syllabus order.
        let q = deck.queue(d(12), Some("mixed"), None);
        assert_eq!(q.items[0].c, 1);
    }

    #[test]
    fn cards_introduced_today_use_up_the_allowance() {
        let cards: Vec<Flashcard> = (1..=40).map(|i| card(i, 10)).collect();
        let states: Vec<CardState> = (1..=12).map(|i| state(i, d(13), d(12))).collect();
        let deck = deck(cards, states);
        let q = deck.queue(d(12), None, None);
        assert_eq!(q.new, 8, "20 - 12 introduced today");
        assert_eq!(q.due, 0, "they are not due until tomorrow");
        assert!(q.items.iter().all(|u| u.c > 12));
        // Tomorrow the allowance is back, and the 12 are due.
        let q = deck.queue(d(13), None, None);
        assert_eq!((q.due, q.new), (12, 20));
        assert_eq!(q.items.len(), 32);
    }

    #[test]
    fn due_cards_come_first_oldest_first() {
        let cards: Vec<Flashcard> = (1..=5).map(|i| card(i, 10)).collect();
        let states = vec![state(3, d(10), d(1)), state(1, d(11), d(1)), state(2, d(20), d(1))];
        let q = deck(cards, states).queue(d(12), None, None);
        let ids: Vec<i64> = q.items.iter().map(|u| u.c).collect();
        assert_eq!(&ids[..2], &[3, 1], "card 2 is not due until the 20th");
        assert_eq!(q.due, 2);
        assert_eq!(&ids[2..], &[4, 5], "new cards: those without a state");
    }

    #[test]
    fn a_subject_filter_limits_due_and_new_cards() {
        let cards = vec![card(1, 10), card(2, 10), card(3, 20), card(4, 20)];
        let states = vec![state(1, d(10), d(1)), state(3, d(10), d(1))];
        let q = deck(cards, states).queue(d(12), None, Some("biology"));
        let ids: Vec<i64> = q.items.iter().map(|u| u.c).collect();
        assert_eq!(ids, [3, 4]);
        assert_eq!((q.due, q.new), (1, 1));
    }

    #[test]
    fn archived_cards_are_not_reviewed() {
        // Only active cards are loaded into a deck; a state of a removed card is ignored.
        let q = deck(vec![card(1, 10)], vec![state(99, d(1), d(1))]).queue(d(12), None, None);
        assert_eq!(q.due, 0);
        assert_eq!(q.new, 1);
    }

    #[test]
    fn stats_count_boxes_due_and_new_per_subject() {
        let cards = vec![card(1, 10), card(2, 10), card(3, 10), card(4, 20)];
        let mut s1 = state(1, d(12), d(1));
        s1.r#box = 1;
        let mut s2 = state(2, d(20), d(1));
        s2.r#box = 5;
        let stats = deck(cards, vec![s1, s2]).stats(d(12));
        assert_eq!(stats[0].slug, "math");
        assert_eq!((stats[0].total, stats[0].new, stats[0].due), (3, 1, 1));
        assert_eq!(stats[0].boxes, [1, 0, 0, 0, 1]);
        assert_eq!((stats[1].total, stats[1].new, stats[1].due), (1, 1, 0));
    }
}
