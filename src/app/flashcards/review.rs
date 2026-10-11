//! The review session: a live component that walks through today's queue.
//!
//! The state (signed, not secret) holds only the queue of card ids, where the student is in
//! it and what they clicked on the current card. The card itself is read from the database
//! every time the component is drawn. Every action carries the position it was drawn for, so
//! a double key press or a stale tab cannot grade a card twice.

use super::card::{self, CLOZE, MATCH, OCCLUSION, ORDER};
use super::deck::{Unit, public_dir};
use super::grading;
use super::leitner::{self, Grade};
use super::svg;
use crate::app::content::models::{Flashcard, Subject, Topic};
use renox::live_component::LiveContext;
use renox::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Default, Debug, Clone)]
pub struct Review {
    pub user_id: i64,
    pub queue: Vec<Unit>,
    pub pos: usize,
    pub revealed: bool,
    /// How many times each grade was given: Again, Hard, Good, Easy.
    pub counts: [u32; 4],
    /// Order cards: the shuffled positions the student has clicked so far.
    pub picked: Vec<usize>,
    /// Match cards: the left item selected, the left items matched, wrong tries.
    pub selected: Option<usize>,
    pub matched: Vec<usize>,
    pub mistakes: u32,
}

impl Review {
    pub fn new(user_id: i64, queue: Vec<Unit>) -> Review {
        Review {
            user_id,
            queue,
            ..Default::default()
        }
    }

    fn finished(&self) -> bool {
        self.pos >= self.queue.len()
    }

    fn reset_card(&mut self) {
        self.revealed = false;
        self.picked.clear();
        self.selected = None;
        self.matched.clear();
        self.mistakes = 0;
    }

    fn unit(&self) -> Option<&Unit> {
        self.queue.get(self.pos)
    }

    /// Only the student reviews, and only their own queue.
    fn check(&self, ctx: &LiveContext, pos: i64) -> Result<bool> {
        let user = ctx.user()?;
        if !user.has_role(crate::app::accounts::STUDENT) || user.id != self.user_id {
            return Err(Error::Forbidden);
        }
        // false: the page was drawn for another card; ignore the click.
        Ok(usize::try_from(pos).is_ok_and(|p| p == self.pos) && !self.finished())
    }

    async fn card(&self, db: &Db) -> Result<Option<Flashcard>> {
        match self.unit() {
            Some(u) => Flashcard::find(db, u.c).await,
            None => Ok(None),
        }
    }
}

fn strings(value: &renox::serde_json::Value, key: &str) -> Vec<String> {
    value
        .get(key)
        .and_then(|v| v.as_array())
        .map(|a| {
            a.iter()
                .filter_map(|x| x.as_str().map(str::to_owned))
                .collect()
        })
        .unwrap_or_default()
}

fn pairs(value: &renox::serde_json::Value) -> Vec<(String, String)> {
    value
        .get("pairs")
        .and_then(|v| v.as_array())
        .map(|a| {
            a.iter()
                .filter_map(|p| {
                    let p = p.as_array()?;
                    Some((
                        p.first()?.as_str()?.to_owned(),
                        p.get(1)?.as_str()?.to_owned(),
                    ))
                })
                .collect()
        })
        .unwrap_or_default()
}

/// The order cards are shown in, stable for a card.
fn order_perm(card: &Flashcard, n: usize) -> Vec<usize> {
    card::shuffled(n, card.id as u64)
}

fn match_perm(card: &Flashcard, n: usize) -> Vec<usize> {
    card::shuffled(n, card.id as u64 ^ 0x5bd1_e995)
}

#[renox::live_component(view = "flashcards/review-live.html", name = "flashcard-review")]
impl Review {
    async fn data(&self, ctx: &LiveContext) -> Result<renox::serde_json::Value> {
        let total = self.queue.len();
        let summary = json!({
            "again": self.counts[0],
            "hard": self.counts[1],
            "good": self.counts[2],
            "easy": self.counts[3],
            "total": self.counts.iter().sum::<u32>(),
        });
        let Some(card) = self.card(&ctx.state().db).await? else {
            return Ok(json!({ "finished": true, "summary": summary, "total": total }));
        };
        let db = &ctx.state().db;
        let topic = Topic::find(db, card.topic_id).await?;
        let subject = match &topic {
            Some(t) => Subject::find(db, t.subject_id).await?,
            None => None,
        };
        let label = self.unit().map(|u| u.l.clone()).unwrap_or_default();
        let state = grading::find_state(db, self.user_id, card.id, &label).await?;
        let box_ = state.as_ref().map_or(leitner::MIN_BOX, |s| s.r#box);

        // The picture: occlusion cards are drawn inline with one label hidden.
        let mut svg_inline: Option<String> = None;
        if card.card_type == OCCLUSION
            && !label.is_empty()
            && let Some(visual) = card.visual.as_deref()
            && let Some(picture) = svg::read(&public_dir(), visual)
        {
            let color = subject.as_ref().map_or("#2563eb", |s| s.color.as_str());
            svg_inline = Some(if self.revealed {
                svg::mark_label(&picture, &label, color)
            } else {
                svg::hide_label(&picture, &label)
            });
        }
        let visual_url = card.visual.as_deref().map(card::visual_url);

        let payload = &card.payload.0;
        let mut view = json!({
            "id": card.id,
            "kind": card.card_type,
            "front": card.front,
            "back": card.back,
            "visual": if svg_inline.is_some() { None } else { visual_url },
            "svg": svg_inline,
            "sketch": card.sketch_prompt,
            "label": label,
            "topic": topic.as_ref().map(|t| t.name.clone()),
            "subject": subject.as_ref().map(|s| json!({
                "slug": s.slug, "name": s.name, "color": s.color, "emoji": s.emoji,
            })),
            "is_new": state.is_none(),
            "box": box_,
        });
        let mut suggested: Option<Grade> = None;
        match card.card_type.as_str() {
            CLOZE => {
                view["parts"] = json!(card::cloze_parts(&card.front));
            }
            ORDER => {
                let items = strings(payload, "items");
                let perm = order_perm(&card, items.len());
                let shown: Vec<_> = perm
                    .iter()
                    .enumerate()
                    .map(|(pos, &i)| {
                        let rank = self.picked.iter().position(|p| *p == pos).map(|r| r + 1);
                        json!({ "pos": pos, "text": items[i], "rank": rank })
                    })
                    .collect();
                let right = self.picked.len() == items.len()
                    && self.picked.iter().enumerate().all(|(r, p)| perm[*p] == r);
                view["shuffled"] = json!(shown);
                view["answer"] = json!(items);
                view["picked"] = json!(self.picked.len());
                view["right"] = json!(right);
                if self.revealed && !items.is_empty() {
                    suggested = Some(if right { Grade::Good } else { Grade::Again });
                }
            }
            MATCH => {
                let list = pairs(payload);
                let perm = match_perm(&card, list.len());
                let left: Vec<_> = list
                    .iter()
                    .enumerate()
                    .map(|(i, (l, _))| {
                        json!({
                            "i": i, "text": l,
                            "matched": self.matched.contains(&i),
                            "selected": self.selected == Some(i),
                        })
                    })
                    .collect();
                let right: Vec<_> = perm
                    .iter()
                    .enumerate()
                    .map(|(j, &i)| {
                        json!({ "j": j, "text": list[i].1, "matched": self.matched.contains(&i) })
                    })
                    .collect();
                view["left"] = json!(left);
                view["right_items"] = json!(right);
                view["pairs"] = json!(list);
                view["mistakes"] = json!(self.mistakes);
                view["done"] = json!(self.matched.len() == list.len());
                if self.revealed && !list.is_empty() {
                    suggested = Some(match self.mistakes {
                        0 if self.matched.len() == list.len() => Grade::Good,
                        0..=2 if self.matched.len() == list.len() => Grade::Hard,
                        _ => Grade::Again,
                    });
                }
            }
            _ => {}
        }
        let buttons: Vec<_> = Grade::ALL
            .iter()
            .map(|g| {
                json!({
                    "n": g.number(),
                    "label": g.label(),
                    "when": leitner::preview(box_, *g),
                    "suggested": suggested == Some(*g),
                })
            })
            .collect();
        Ok(json!({
            "finished": false,
            "total": total,
            "number": self.pos + 1,
            "percent": (self.pos * 100).checked_div(total).unwrap_or(0),
            "card": view,
            "buttons": buttons,
            "summary": summary,
        }))
    }

    /// Show the back of the card.
    #[live(action)]
    async fn reveal(&mut self, ctx: &mut LiveContext, pos: i64) -> Result {
        if self.check(ctx, pos)? {
            self.revealed = true;
        }
        Ok(())
    }

    /// Order cards: click the next item (by its position on screen).
    #[live(action)]
    async fn pick(&mut self, ctx: &mut LiveContext, pos: i64, item: i64) -> Result {
        if !self.check(ctx, pos)? || self.revealed {
            return Ok(());
        }
        let Some(card) = self.card(&ctx.state().db).await? else {
            return Ok(());
        };
        let n = strings(&card.payload.0, "items").len();
        let item = usize::try_from(item).map_err(|_| Error::BadRequest("bad item".into()))?;
        if item < n && !self.picked.contains(&item) {
            self.picked.push(item);
            if self.picked.len() == n {
                self.revealed = true;
            }
        }
        Ok(())
    }

    /// Order cards: start again.
    #[live(action)]
    async fn clear_picks(&mut self, ctx: &mut LiveContext, pos: i64) -> Result {
        if self.check(ctx, pos)? && !self.revealed {
            self.picked.clear();
        }
        Ok(())
    }

    /// Match cards: select an item of the left column.
    #[live(action)]
    async fn choose_left(&mut self, ctx: &mut LiveContext, pos: i64, item: i64) -> Result {
        if !self.check(ctx, pos)? || self.revealed {
            return Ok(());
        }
        let item = usize::try_from(item).map_err(|_| Error::BadRequest("bad item".into()))?;
        if !self.matched.contains(&item) {
            self.selected = if self.selected == Some(item) {
                None
            } else {
                Some(item)
            };
        }
        Ok(())
    }

    /// Match cards: click an item of the right column (by its position on screen).
    #[live(action)]
    async fn choose_right(&mut self, ctx: &mut LiveContext, pos: i64, item: i64) -> Result {
        if !self.check(ctx, pos)? || self.revealed {
            return Ok(());
        }
        let (Some(left), Some(card)) = (self.selected, self.card(&ctx.state().db).await?) else {
            return Ok(());
        };
        let n = pairs(&card.payload.0).len();
        let item = usize::try_from(item).map_err(|_| Error::BadRequest("bad item".into()))?;
        if item >= n {
            return Err(Error::BadRequest("bad item".into()));
        }
        let real = match_perm(&card, n)[item];
        if self.matched.contains(&real) {
            return Ok(());
        }
        if real == left {
            self.matched.push(left);
            if self.matched.len() == n {
                self.revealed = true;
            }
        } else {
            self.mistakes += 1;
        }
        self.selected = None;
        Ok(())
    }

    /// Grade the card (1 Again, 2 Hard, 3 Good, 4 Easy) and move on.
    #[live(action)]
    async fn grade(&mut self, ctx: &mut LiveContext, pos: i64, number: i64) -> Result {
        if !self.check(ctx, pos)? || !self.revealed {
            return Ok(());
        }
        let grade = Grade::from_number(number)
            .ok_or_else(|| Error::BadRequest("The grade is 1 to 4.".into()))?;
        let unit = self.queue[self.pos].clone();
        let db = ctx.state().db.clone();
        if Flashcard::find(&db, unit.c).await?.is_some() {
            grading::record(
                &db,
                self.user_id,
                unit.c,
                &unit.l,
                grade,
                crate::clock::today(),
            )
            .await?;
        }
        self.counts[(number - 1) as usize] += 1;
        self.pos += 1;
        self.reset_card();
        Ok(())
    }
}

/// A new session over today's queue (optionally one subject).
pub async fn new_session(
    db: &Db,
    user_id: i64,
    today: renox::chrono::NaiveDate,
    only: Option<&str>,
) -> Result<Review> {
    let queue = super::deck::queue_for(db, user_id, today, only).await?;
    Ok(Review::new(user_id, queue.items))
}
