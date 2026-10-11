//! Small pure helpers for the card types: cloze gaps, shuffles, and the picture URL.

use serde::Serialize;

pub const BASIC: &str = "basic";
pub const CLOZE: &str = "cloze";
pub const ORDER: &str = "order";
pub const MATCH: &str = "match";
pub const OCCLUSION: &str = "occlusion";

/// A piece of a cloze card's front: plain text, or the text of a `{{gap}}`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ClozePart {
    pub text: String,
    pub gap: bool,
}

/// Splits `The {{left ventricle}} pumps blood` into text and gap parts.
/// An unclosed `{{` stays plain text.
pub fn cloze_parts(front: &str) -> Vec<ClozePart> {
    let mut parts = Vec::new();
    let mut rest = front;
    while let Some(open) = rest.find("{{") {
        let Some(len) = rest[open + 2..].find("}}") else {
            break;
        };
        if open > 0 {
            parts.push(ClozePart {
                text: rest[..open].to_owned(),
                gap: false,
            });
        }
        parts.push(ClozePart {
            text: rest[open + 2..open + 2 + len].trim().to_owned(),
            gap: true,
        });
        rest = &rest[open + 2 + len + 2..];
    }
    if !rest.is_empty() {
        parts.push(ClozePart {
            text: rest.to_owned(),
            gap: false,
        });
    }
    parts
}

/// The gaps of a cloze card, in order: what the back shows.
pub fn cloze_answers(front: &str) -> Vec<String> {
    cloze_parts(front)
        .into_iter()
        .filter(|p| p.gap)
        .map(|p| p.text)
        .collect()
}

/// A fixed shuffle of `0..n` for `seed` (the same card always shows the same order, so the
/// page can be drawn again after every click). It is never the identity when `n >= 2`.
pub fn shuffled(n: usize, seed: u64) -> Vec<usize> {
    let mut order: Vec<usize> = (0..n).collect();
    let mut state = seed
        .wrapping_mul(6364136223846793005)
        .wrapping_add(1442695040888963407);
    for i in (1..n).rev() {
        state = state
            .wrapping_mul(6364136223846793005)
            .wrapping_add(1442695040888963407);
        let j = (state >> 33) as usize % (i + 1);
        order.swap(i, j);
    }
    if n >= 2 && order.iter().enumerate().all(|(i, v)| i == *v) {
        order.rotate_left(1);
    }
    order
}

/// The URL of a card's picture: a content path (`content/biology/x.svg`, under `public/`)
/// or an upload's URL, which already starts with a slash.
pub fn visual_url(visual: &str) -> String {
    if visual.starts_with('/') || visual.starts_with("http") {
        visual.to_owned()
    } else {
        format!("/{visual}")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn splits_cloze_gaps() {
        let parts = cloze_parts("The {{ left ventricle }} pumps blood to the {{aorta}}.");
        assert_eq!(
            parts,
            vec![
                ClozePart { text: "The ".into(), gap: false },
                ClozePart { text: "left ventricle".into(), gap: true },
                ClozePart { text: " pumps blood to the ".into(), gap: false },
                ClozePart { text: "aorta".into(), gap: true },
                ClozePart { text: ".".into(), gap: false },
            ]
        );
        assert_eq!(cloze_answers("A {{b}} c {{d}}"), ["b", "d"]);
    }

    #[test]
    fn cloze_without_gaps_or_with_an_open_gap_is_plain_text() {
        assert_eq!(
            cloze_parts("no gaps"),
            vec![ClozePart { text: "no gaps".into(), gap: false }]
        );
        let open = cloze_parts("half {{open");
        assert!(open.iter().all(|p| !p.gap));
        assert_eq!(cloze_parts(""), vec![]);
    }

    #[test]
    fn a_gap_can_start_the_text() {
        let parts = cloze_parts("{{ATP}} is energy");
        assert_eq!(parts[0], ClozePart { text: "ATP".into(), gap: true });
        assert_eq!(parts.len(), 2);
    }

    #[test]
    fn shuffles_are_stable_permutations_and_never_the_identity() {
        for n in 2..9 {
            for seed in 0..40u64 {
                let a = shuffled(n, seed);
                assert_eq!(a, shuffled(n, seed), "stable");
                let mut sorted = a.clone();
                sorted.sort_unstable();
                assert_eq!(sorted, (0..n).collect::<Vec<_>>(), "a permutation");
                assert_ne!(a, (0..n).collect::<Vec<_>>(), "n={n} seed={seed}");
            }
        }
        assert_eq!(shuffled(1, 3), [0]);
        assert_eq!(shuffled(0, 3), Vec::<usize>::new());
    }

    #[test]
    fn urls_for_content_and_uploads() {
        assert_eq!(visual_url("content/biology/x.svg"), "/content/biology/x.svg");
        assert_eq!(visual_url("/storage/flashcards/a.png"), "/storage/flashcards/a.png");
    }
}
