//! Reading the lesson files in `materi/<subject>/*.md`.
//!
//! A lesson file starts with a heading that names its subtopic (`# 🟩 Nervous System  ·
//! `biology.anatomy.nervous``), has a "Watch / try" list of links and ends with a "Check your
//! understanding" section: five questions (`**1.** …` then `(A) … (E) …`) and an answer key
//! inside `<details>` (`1. **(B) axon.** …`). Nothing here touches the database.

use serde::{Deserialize, Serialize};
use std::path::Path;

/// Files in `materi/<subject>/` that are not lessons (the folder guide and the cheat sheet).
pub const NOT_LESSONS: [&str; 2] = ["README.md", "lembar-ringkas.md"];

/// A link of the "Watch / try" list.
#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct WatchLink {
    pub label: String,
    pub url: String,
    /// The text after the link ("Amoeba Sisters · 11:32 · ...").
    pub note: String,
}

/// One question of the "Check your understanding" section.
#[derive(Debug, Clone, Default, Serialize, PartialEq)]
pub struct CheckQuestion {
    pub number: usize,
    pub text: String,
    /// The five choices as `(letter, text)`.
    pub choices: Vec<(String, String)>,
    /// The right letter, from the answer key.
    pub answer: String,
    /// The key line after the number, as Markdown: `**(B) axon.** The axon is ...`.
    pub explanation: String,
}

/// A lesson file, parsed. `problems` lists everything wrong with it.
#[derive(Debug, Clone, Default)]
pub struct LessonFile {
    /// Path relative to the project (`materi/biology/anatomy-nervous.md`).
    pub path: String,
    /// The folder name (`biology`).
    pub subject: String,
    pub slug: String,
    pub title: String,
    pub markdown: String,
    pub watch_links: Vec<WatchLink>,
    pub questions: Vec<CheckQuestion>,
    pub problems: Vec<String>,
}

/// Everything the lesson page needs from a lesson's Markdown.
#[derive(Debug, Clone, Default)]
pub struct ParsedLesson {
    pub slug: String,
    pub title: String,
    /// The material (everything before the Check section).
    pub body: String,
    /// The `<details>` answer key, as Markdown/HTML for the renderer.
    pub key_block: String,
    pub watch_links: Vec<WatchLink>,
    pub questions: Vec<CheckQuestion>,
    pub problems: Vec<String>,
}

/// Is `s` a dotted slug like `biology.cell.division` (three lowercase parts)?
pub fn is_slug(s: &str) -> bool {
    let parts: Vec<&str> = s.split('.').collect();
    parts.len() == 3
        && parts.iter().all(|p| {
            !p.is_empty()
                && p.chars()
                    .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
        })
}

/// Parses the first heading: the title and the slug between backticks.
fn parse_heading(markdown: &str, problems: &mut Vec<String>) -> (String, String) {
    let Some(first) = markdown.lines().find(|l| !l.trim().is_empty()) else {
        problems.push("the file is empty".into());
        return Default::default();
    };
    let Some(heading) = first.strip_prefix("# ") else {
        problems
            .push("the first line must be a `# Title  ·  `subject.topic.subtopic`` heading".into());
        return Default::default();
    };
    let slug = heading
        .split('`')
        .nth(1)
        .map(str::trim)
        .unwrap_or_default()
        .to_owned();
    if !is_slug(&slug) {
        problems.push(format!(
            "the heading must name the subtopic in backticks (`subject.topic.subtopic`), found `{slug}`"
        ));
    }
    let before = heading.split('`').next().unwrap_or_default();
    let before = before.trim().trim_end_matches('·').trim();
    // Drop the colour emoji in front of the title.
    let title = match before.split_once(' ') {
        Some((first_word, rest)) if !first_word.chars().any(char::is_alphanumeric) => rest.trim(),
        _ => before,
    };
    (title.to_owned(), slug)
}

fn parse_watch(markdown: &str) -> Vec<WatchLink> {
    let mut in_section = false;
    let mut links = Vec::new();
    for line in markdown.lines() {
        if line.starts_with("## ") {
            in_section = line.contains("Watch / try");
            continue;
        }
        if !in_section {
            continue;
        }
        let Some(rest) = line.trim().strip_prefix("- [") else {
            continue;
        };
        let Some((label, rest)) = rest.split_once("](") else {
            continue;
        };
        let Some((url, note)) = rest.split_once(')') else {
            continue;
        };
        links.push(WatchLink {
            label: label.to_owned(),
            url: url.to_owned(),
            note: note
                .trim()
                .trim_start_matches(['—', '-', '–'])
                .trim()
                .to_owned(),
        });
    }
    links
}

/// Splits `(A) text  (B) text ...` into five choices, or `None` when it is not that shape.
fn parse_choices(line: &str) -> Option<Vec<(String, String)>> {
    let line = line.trim();
    if !line.starts_with("(A) ") {
        return None;
    }
    let mut starts = vec![0usize];
    for letter in ['B', 'C', 'D', 'E'] {
        let marker = format!(" ({letter}) ");
        let from = *starts.last()?;
        let at = line[from..].find(&marker)? + from;
        starts.push(at + 1);
    }
    let mut out = Vec::new();
    for (i, start) in starts.iter().enumerate() {
        let end = starts.get(i + 1).copied().unwrap_or(line.len());
        let piece = line[*start..end].trim();
        let text = piece.get(4..)?.trim();
        out.push((((b'A' + i as u8) as char).to_string(), text.to_owned()));
    }
    Some(out)
}

/// Parses a lesson's Markdown. Never fails: what is wrong goes to `problems`.
pub fn parse_lesson(markdown: &str) -> ParsedLesson {
    let mut p = ParsedLesson::default();
    let (title, slug) = parse_heading(markdown, &mut p.problems);
    p.title = title;
    p.slug = slug;
    p.watch_links = parse_watch(markdown);

    // The Check section starts at the heading that mentions it.
    let lines: Vec<&str> = markdown.lines().collect();
    let check_at = lines
        .iter()
        .position(|l| l.starts_with("## ") && l.contains("Check your understanding"));
    let Some(check_at) = check_at else {
        p.problems
            .push("there is no `## ✅ Check your understanding` section".into());
        p.body = markdown.to_owned();
        return p;
    };
    p.body = lines[..check_at].join("\n");
    let section = &lines[check_at + 1..];
    let details_at = section
        .iter()
        .position(|l| l.trim().starts_with("<details"));
    let (before, key_lines): (&[&str], &[&str]) = match details_at {
        Some(i) => (&section[..i], &section[i..]),
        None => (section, &[]),
    };
    p.key_block = key_lines.join("\n");
    if details_at.is_none() {
        p.problems
            .push("the Check section has no `<details>` answer key".into());
    }

    // Questions: `**N.** text` (maybe several lines) followed by the `(A) … (E) …` line.
    let mut questions: Vec<CheckQuestion> = Vec::new();
    let mut current: Option<CheckQuestion> = None;
    let mut buf = String::new();
    for line in before {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if let Some(rest) = line.strip_prefix("**")
            && let Some((num, text)) = rest.split_once(".**")
            && let Ok(number) = num.parse::<usize>()
        {
            if let Some(mut q) = current.take() {
                q.choices = parse_choices(&buf).unwrap_or_default();
                questions.push(q);
            }
            buf.clear();
            current = Some(CheckQuestion {
                number,
                text: text.trim().to_owned(),
                ..Default::default()
            });
        } else if let Some(q) = current.as_mut() {
            // The choices are on one line `(A) … (B) …` or one per line.
            if !buf.is_empty() || line.starts_with("(A) ") {
                if !buf.is_empty() {
                    buf.push_str("  ");
                }
                buf.push_str(line);
            } else {
                q.text.push('\n');
                q.text.push_str(line);
            }
        }
    }
    if let Some(mut q) = current.take() {
        q.choices = parse_choices(&buf).unwrap_or_default();
        questions.push(q);
    }

    // The answer key: `N. **(X) …`.
    for line in key_lines {
        let line = line.trim();
        let Some((num, rest)) = line.split_once(". **(") else {
            continue;
        };
        let (Ok(number), Some(letter)) = (num.parse::<usize>(), rest.chars().next()) else {
            continue;
        };
        if let Some(q) = questions.iter_mut().find(|q| q.number == number) {
            q.answer = letter.to_string();
            q.explanation = format!("**({rest}");
        }
    }

    if questions.len() != 5 {
        p.problems.push(format!(
            "the Check section must have 5 questions (`**1.** …`), found {}",
            questions.len()
        ));
    }
    for (i, q) in questions.iter().enumerate() {
        if q.number != i + 1 {
            p.problems.push(format!(
                "question {} is numbered {} (they must be 1-5 in order)",
                i + 1,
                q.number
            ));
        }
        if q.choices.len() != 5 {
            p.problems.push(format!(
                "question {} needs five choices `(A) … (E) …`",
                q.number
            ));
        }
        if q.answer.is_empty() {
            p.problems.push(format!(
                "question {} has no line `{}. **(X) …` in the answer key",
                q.number, q.number
            ));
        }
    }
    p.questions = questions;
    p
}

/// The `public/content/…` image paths a lesson uses (`../../public/content/biology/x.svg`).
pub fn image_paths(markdown: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut rest = markdown;
    while let Some(at) = rest.find("](") {
        rest = &rest[at + 2..];
        let end = rest.find(')').unwrap_or(rest.len());
        let target = &rest[..end];
        if let Some(path) = target.strip_prefix("../../public/") {
            out.push(path.to_owned());
        }
    }
    out
}

/// Reads one lesson file. `root` is the project directory.
pub fn read_lesson(root: &Path, path: &Path) -> Result<LessonFile, String> {
    let markdown = std::fs::read_to_string(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let parsed = parse_lesson(&markdown);
    let rel = path
        .strip_prefix(root)
        .unwrap_or(path)
        .to_string_lossy()
        .into_owned();
    let subject = path
        .parent()
        .and_then(Path::file_name)
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    Ok(LessonFile {
        path: rel,
        subject,
        slug: parsed.slug,
        title: parsed.title,
        markdown,
        watch_links: parsed.watch_links,
        questions: parsed.questions,
        problems: parsed.problems,
    })
}

/// Loads every `materi/<subject>/*.md` lesson. A missing `materi/` or subject folder is fine.
pub fn load_lessons(root: &Path) -> Result<Vec<LessonFile>, String> {
    let materi = root.join("materi");
    let mut dirs: Vec<_> = std::fs::read_dir(&materi)
        .map(|rd| rd.filter_map(|e| e.ok()).map(|e| e.path()).collect())
        .unwrap_or_default();
    dirs.sort();
    let mut lessons = Vec::new();
    for dir in dirs.into_iter().filter(|d| d.is_dir()) {
        let mut files: Vec<_> = std::fs::read_dir(&dir)
            .map(|rd| {
                rd.filter_map(|e| e.ok())
                    .map(|e| e.path())
                    .filter(|p| p.extension().is_some_and(|x| x == "md"))
                    .collect()
            })
            .unwrap_or_default();
        files.sort();
        for file in files {
            let name = file
                .file_name()
                .map(|n| n.to_string_lossy().into_owned())
                .unwrap_or_default();
            if NOT_LESSONS.contains(&name.as_str()) {
                continue;
            }
            lessons.push(read_lesson(root, &file)?);
        }
    }
    Ok(lessons)
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE: &str = "# 🟩 Nervous System  ·  `biology.anatomy.nervous`\n\nIntro.\n\n## 🎥 Watch / try\n- [Video](https://example.com/v) — Someone · 3:00 · notes\n\n## ✅ Check your understanding (5 questions)\n\n**1.** First?\n\n(A) a  (B) b  (C) c  (D) d  (E) e\n\n**2.** Second?\n\n(A) a  (B) b  (C) c  (D) d  (E) e\n\n**3.** Third?\n\n(A) a  (B) b  (C) c  (D) d  (E) e\n\n**4.** Fourth?\n\n(A) a  (B) b  (C) c  (D) d  (E) e\n\n**5.** Fifth?\n\n(A) a  (B) b  (C) c  (D) d  (E) e\n\n<details><summary>Key</summary>\n\n1. **(B) b.** why\n2. **(A) a.** why\n3. **(C) c.** why\n4. **(D) d.** why\n5. **(E) e.** why\n</details>\n";

    #[test]
    fn parses_a_good_lesson() {
        let p = parse_lesson(SAMPLE);
        assert!(p.problems.is_empty(), "{:?}", p.problems);
        assert_eq!(p.slug, "biology.anatomy.nervous");
        assert_eq!(p.title, "Nervous System");
        assert_eq!(p.questions.len(), 5);
        assert_eq!(p.questions[0].answer, "B");
        assert_eq!(p.questions[4].choices[4], ("E".to_owned(), "e".to_owned()));
        assert_eq!(p.watch_links[0].url, "https://example.com/v");
        assert!(p.watch_links[0].note.starts_with("Someone"));
        assert!(!p.body.contains("Check your understanding"));
        assert!(p.key_block.starts_with("<details>"));
    }

    #[test]
    fn reports_a_wrong_slug_and_missing_questions() {
        let p = parse_lesson("# 🟩 Oops  ·  `not a slug`\n\n## ✅ Check your understanding\n");
        let all = p.problems.join("\n");
        assert!(all.contains("must name the subtopic"), "{all}");
        assert!(all.contains("5 questions"), "{all}");
        assert!(all.contains("<details>"), "{all}");
    }
}
