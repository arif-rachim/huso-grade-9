//! Reading and validating the content files in `content/` (the source of truth).
//!
//! `load_all` parses every file, `validate` returns human-readable problems (an empty list
//! means the content is good). Nothing here touches the database.

use renox::chrono::NaiveDate;
use renox::serde_json::{Map, Value};
use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet, HashSet};
use std::path::{Path, PathBuf};

pub const SUBJECTS: [&str; 5] = ["math", "physics", "chemistry", "biology", "earth"];
/// `subject` values of a plan day that are not a school subject.
pub const PLAN_EXTRA_SUBJECTS: [&str; 5] = ["diagnostic", "mixed", "review", "prep", "exam"];
pub const PLAN_PHASES: [&str; 5] = ["intensive", "daily", "weekend", "readiness", "exam"];
pub const CARD_TYPES: [&str; 5] = ["basic", "cloze", "order", "match", "occlusion"];

#[derive(Debug, Deserialize)]
pub struct Syllabus {
    pub subjects: Vec<SyllabusSubject>,
}

#[derive(Debug, Deserialize)]
pub struct SyllabusSubject {
    pub slug: String,
    pub name: String,
    pub color: String,
    pub emoji: String,
    #[serde(default)]
    pub level_hint: Option<String>,
    pub topics: Vec<SyllabusTopic>,
}

#[derive(Debug, Deserialize)]
pub struct SyllabusTopic {
    pub slug: String,
    pub name: String,
    #[serde(default)]
    pub children: Vec<SyllabusSubtopic>,
}

#[derive(Debug, Deserialize)]
pub struct SyllabusSubtopic {
    pub slug: String,
    pub name: String,
    #[serde(default)]
    pub items: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct Plan {
    pub days: Vec<PlanDayFile>,
}

#[derive(Debug, Deserialize)]
pub struct PlanDayFile {
    pub date: String,
    pub phase: String,
    pub minutes: i64,
    pub subject: String,
    pub title: String,
    #[serde(default)]
    pub issue: Option<i64>,
    #[serde(default)]
    pub new_subtopics: Vec<String>,
    #[serde(default)]
    pub blocks: Vec<PlanBlockFile>,
}

#[derive(Debug, Deserialize)]
pub struct PlanBlockFile {
    pub label: String,
    pub minutes: i64,
    #[serde(default)]
    pub tasks: Vec<String>,
    #[serde(default)]
    pub subtopics: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct FlashcardFile {
    pub subject: String,
    pub cards: Vec<CardFile>,
}

#[derive(Debug, Deserialize)]
pub struct CardFile {
    pub id: String,
    pub subtopic: String,
    #[serde(rename = "type")]
    pub kind: String,
    #[serde(default)]
    pub front: String,
    #[serde(default)]
    pub back: String,
    #[serde(default)]
    pub visual: Option<String>,
    #[serde(default)]
    pub sketch_prompt: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    /// `items`, `pairs`, and anything else a card type needs.
    #[serde(flatten)]
    pub extra: Map<String, Value>,
}

#[derive(Debug, Deserialize)]
pub struct QuestionFile {
    pub subject: String,
    pub questions: Vec<QuestionEntry>,
}

#[derive(Debug, Deserialize)]
pub struct QuestionEntry {
    pub id: String,
    pub subtopic: String,
    pub difficulty: i64,
    pub stem: String,
    #[serde(default)]
    pub visual: Option<String>,
    pub choices: BTreeMap<String, String>,
    pub answer: String,
    pub explanation: String,
    #[serde(default)]
    pub explanation_visual: Option<String>,
    #[serde(default = "original")]
    pub source: String,
}

fn original() -> String {
    "original".to_owned()
}

/// Everything under `content/`, parsed.
#[derive(Debug)]
pub struct ContentBundle {
    /// The project directory (holds `content/` and `public/`).
    pub root: PathBuf,
    pub syllabus: Syllabus,
    pub plan: Plan,
    pub flashcards: Vec<FlashcardFile>,
    pub questions: Vec<QuestionFile>,
}

fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, String> {
    let text = std::fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    renox::serde_json::from_str(&text).map_err(|e| format!("{}: {e}", path.display()))
}

fn json_files(dir: &Path) -> Vec<PathBuf> {
    let mut files: Vec<PathBuf> = std::fs::read_dir(dir)
        .map(|rd| {
            rd.filter_map(|e| e.ok())
                .map(|e| e.path())
                .filter(|p| p.extension().is_some_and(|x| x == "json"))
                .collect()
        })
        .unwrap_or_default();
    files.sort();
    files
}

/// Parses `content/syllabus.json`, `plan.json`, `flashcards/*.json` and `questions/*.json`.
pub fn load_all(root: &Path) -> Result<ContentBundle, String> {
    let content = root.join("content");
    let syllabus = read_json(&content.join("syllabus.json"))?;
    let plan = read_json(&content.join("plan.json"))?;
    let flashcards = json_files(&content.join("flashcards"))
        .iter()
        .map(|p| read_json(p))
        .collect::<Result<_, _>>()?;
    let questions = json_files(&content.join("questions"))
        .iter()
        .map(|p| read_json(p))
        .collect::<Result<_, _>>()?;
    Ok(ContentBundle {
        root: root.to_owned(),
        syllabus,
        plan,
        flashcards,
        questions,
    })
}

impl ContentBundle {
    /// Slugs of the level-2 topics (the units whose mastery is tracked).
    pub fn subtopic_slugs(&self) -> BTreeSet<&str> {
        self.syllabus
            .subjects
            .iter()
            .flat_map(|s| &s.topics)
            .flat_map(|t| &t.children)
            .map(|c| c.slug.as_str())
            .collect()
    }
}

/// Checks that a `public/…` visual exists, is an SVG and is safe. Pushes problems to `errors`.
fn check_visual(root: &Path, what: &str, visual: &Option<String>, errors: &mut Vec<String>) {
    let Some(path) = visual else { return };
    if !path.ends_with(".svg") {
        errors.push(format!("{what}: visual `{path}` is not an .svg file"));
        return;
    }
    let file = root.join("public").join(path);
    match std::fs::read_to_string(&file) {
        Err(_) => errors.push(format!(
            "{what}: visual `{path}` does not exist under public/"
        )),
        Ok(svg) => {
            if svg.contains("<script") {
                errors.push(format!("{what}: `{path}` contains a <script>"));
            }
            if svg.contains("href=\"http") || svg.contains("href='http") {
                errors.push(format!("{what}: `{path}` has an external href"));
            }
        }
    }
}

fn check_unique<'a>(
    kind: &str,
    ids: impl Iterator<Item = &'a str>,
    errors: &mut Vec<String>,
) -> HashSet<&'a str> {
    let mut seen = HashSet::new();
    for id in ids {
        if !seen.insert(id) {
            errors.push(format!("duplicate {kind} `{id}`"));
        }
    }
    seen
}

/// Every problem in the content, as sentences. An empty list means the content is valid.
pub fn validate(bundle: &ContentBundle) -> Vec<String> {
    let mut errors = Vec::new();
    let root = &bundle.root;
    let subtopics = bundle.subtopic_slugs();

    // Syllabus: unique slugs, known subjects, nested slugs.
    let all_slugs = bundle.syllabus.subjects.iter().flat_map(|s| {
        std::iter::once(s.slug.as_str())
            .chain(s.topics.iter().map(|t| t.slug.as_str()))
            .chain(
                s.topics
                    .iter()
                    .flat_map(|t| t.children.iter().map(|c| c.slug.as_str())),
            )
    });
    check_unique("syllabus slug", all_slugs, &mut errors);
    for s in &bundle.syllabus.subjects {
        if !SUBJECTS.contains(&s.slug.as_str()) {
            errors.push(format!("syllabus: unknown subject `{}`", s.slug));
        }
        for t in &s.topics {
            if !t.slug.starts_with(&format!("{}.", s.slug)) {
                errors.push(format!(
                    "syllabus: topic `{}` is not under `{}`",
                    t.slug, s.slug
                ));
            }
            for c in &t.children {
                if !c.slug.starts_with(&format!("{}.", t.slug)) {
                    errors.push(format!(
                        "syllabus: subtopic `{}` is not under `{}`",
                        c.slug, t.slug
                    ));
                }
            }
        }
    }

    // Plan: 35 consecutive days, valid values.
    let days = &bundle.plan.days;
    if days.len() != 35 {
        errors.push(format!("plan: expected 35 days, found {}", days.len()));
    }
    let mut previous: Option<NaiveDate> = None;
    for day in days {
        match NaiveDate::parse_from_str(&day.date, "%Y-%m-%d") {
            Err(_) => errors.push(format!("plan: `{}` is not a date (YYYY-MM-DD)", day.date)),
            Ok(date) => {
                if let Some(prev) = previous
                    && (date - prev).num_days() != 1
                {
                    errors.push(format!("plan: gap or disorder between {prev} and {date}"));
                }
                previous = Some(date);
            }
        }
        if !PLAN_PHASES.contains(&day.phase.as_str()) {
            errors.push(format!("plan {}: unknown phase `{}`", day.date, day.phase));
        }
        if !SUBJECTS.contains(&day.subject.as_str())
            && !PLAN_EXTRA_SUBJECTS.contains(&day.subject.as_str())
        {
            errors.push(format!(
                "plan {}: unknown subject `{}`",
                day.date, day.subject
            ));
        }
        for slug in day
            .new_subtopics
            .iter()
            .chain(day.blocks.iter().flat_map(|b| &b.subtopics))
        {
            if !subtopics.contains(slug.as_str()) {
                errors.push(format!("plan {}: unknown subtopic `{slug}`", day.date));
            }
        }
    }

    // Flashcards.
    check_unique(
        "flashcard id",
        bundle
            .flashcards
            .iter()
            .flat_map(|f| f.cards.iter().map(|c| c.id.as_str())),
        &mut errors,
    );
    for file in &bundle.flashcards {
        if !SUBJECTS.contains(&file.subject.as_str()) {
            errors.push(format!("flashcards: unknown subject `{}`", file.subject));
        }
        for card in &file.cards {
            let what = format!("card {}", card.id);
            if !subtopics.contains(card.subtopic.as_str()) {
                errors.push(format!(
                    "{what}: `{}` is not a subtopic of the syllabus",
                    card.subtopic
                ));
            } else if !card.subtopic.starts_with(&format!("{}.", file.subject)) {
                errors.push(format!(
                    "{what}: subtopic `{}` is not in subject `{}`",
                    card.subtopic, file.subject
                ));
            }
            if !CARD_TYPES.contains(&card.kind.as_str()) {
                errors.push(format!("{what}: unknown type `{}`", card.kind));
            }
            let has_visual = card.visual.as_deref().is_some_and(|v| !v.is_empty());
            let has_sketch = card
                .sketch_prompt
                .as_deref()
                .is_some_and(|v| !v.trim().is_empty());
            if !has_visual && !has_sketch {
                errors.push(format!("{what}: needs a `visual` or a `sketch_prompt`"));
            }
            let count = |key: &str| {
                card.extra
                    .get(key)
                    .and_then(Value::as_array)
                    .map_or(0, Vec::len)
            };
            match card.kind.as_str() {
                "cloze" if !card.front.contains("{{") || !card.front.contains("}}") => {
                    errors.push(format!(
                        "{what}: a cloze card needs a {{{{gap}}}} in `front`"
                    ));
                }
                "order" if count("items") < 3 => {
                    errors.push(format!("{what}: an order card needs at least 3 `items`"))
                }
                "match" if count("pairs") < 3 => {
                    errors.push(format!("{what}: a match card needs at least 3 `pairs`"))
                }
                "occlusion" if !has_visual => {
                    errors.push(format!("{what}: an occlusion card needs a `visual`"))
                }
                _ => {}
            }
            if matches!(card.kind.as_str(), "basic" | "cloze" | "occlusion")
                && (card.front.trim().is_empty() || card.back.trim().is_empty())
            {
                errors.push(format!("{what}: `front` and `back` must not be empty"));
            }
            check_visual(root, &what, &card.visual, &mut errors);
        }
    }

    // Questions.
    check_unique(
        "question id",
        bundle
            .questions
            .iter()
            .flat_map(|f| f.questions.iter().map(|q| q.id.as_str())),
        &mut errors,
    );
    for file in &bundle.questions {
        if !SUBJECTS.contains(&file.subject.as_str()) {
            errors.push(format!("questions: unknown subject `{}`", file.subject));
        }
        for q in &file.questions {
            let what = format!("question {}", q.id);
            if !subtopics.contains(q.subtopic.as_str()) {
                errors.push(format!(
                    "{what}: `{}` is not a subtopic of the syllabus",
                    q.subtopic
                ));
            } else if !q.subtopic.starts_with(&format!("{}.", file.subject)) {
                errors.push(format!(
                    "{what}: subtopic `{}` is not in subject `{}`",
                    q.subtopic, file.subject
                ));
            }
            if !(1..=3).contains(&q.difficulty) {
                errors.push(format!(
                    "{what}: difficulty must be 1-3, found {}",
                    q.difficulty
                ));
            }
            if q.stem.trim().is_empty() || q.explanation.trim().is_empty() {
                errors.push(format!(
                    "{what}: `stem` and `explanation` must not be empty"
                ));
            }
            let letters: Vec<&str> = q.choices.keys().map(String::as_str).collect();
            if letters != ["A", "B", "C", "D", "E"] {
                errors.push(format!(
                    "{what}: choices must be exactly A-E, found {letters:?}"
                ));
            }
            if q.choices.values().any(|c| c.trim().is_empty()) {
                errors.push(format!("{what}: a choice is empty"));
            }
            let distinct: HashSet<&str> = q.choices.values().map(|c| c.trim()).collect();
            if distinct.len() != q.choices.len() {
                errors.push(format!("{what}: two choices are identical"));
            }
            if !["A", "B", "C", "D", "E"].contains(&q.answer.as_str()) {
                errors.push(format!("{what}: answer `{}` is not one of A-E", q.answer));
            }
            if q.source != "original" {
                errors.push(format!(
                    "{what}: source must be `original`, found `{}`",
                    q.source
                ));
            }
            check_visual(root, &what, &q.visual, &mut errors);
            check_visual(root, &what, &q.explanation_visual, &mut errors);
        }
    }
    errors
}
