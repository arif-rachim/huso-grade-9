//! Markdown to safe HTML for the lesson pages.
//!
//! The lesson files are ours, but the page still treats the Markdown as untrusted: raw HTML is
//! escaped except `<details>` and `<summary>` (without attributes), link and image addresses must
//! be `http(s)`, `mailto:`, `/…`, `#…` or relative, and `../../public/content/…` image paths
//! become `/content/…`.

use pulldown_cmark::{CowStr, Event, Options, Parser, Tag, TagEnd, html};
use pulldown_cmark_escape::{escape_href, escape_html};

/// `../../public/content/x.svg` becomes `/content/x.svg`.
pub fn rewrite_image_path(url: &str) -> String {
    let mut rest = url;
    while let Some(r) = rest.strip_prefix("../") {
        rest = r;
    }
    if let Some(r) = rest.strip_prefix("public/") {
        return format!("/{r}");
    }
    url.to_owned()
}

/// Is `url` safe to put in an `href` or `src`?
fn safe_url(url: &str) -> bool {
    let u = url.trim().to_ascii_lowercase();
    // A scheme is everything before the first `:` when no `/`, `?` or `#` comes first.
    match u.find([':', '/', '?', '#']) {
        Some(i) if u.as_bytes()[i] == b':' => {
            matches!(&u[..i], "http" | "https" | "mailto")
        }
        _ => true,
    }
}

/// Emits the allowed tags of a raw HTML chunk and escapes everything else as text.
fn sanitize_raw_html(raw: &str, out: &mut String) {
    let mut rest = raw;
    while let Some(lt) = rest.find('<') {
        let _ = escape_html(&mut *out, &rest[..lt]);
        rest = &rest[lt..];
        let Some(gt) = rest.find('>') else {
            let _ = escape_html(&mut *out, rest);
            return;
        };
        let tag = &rest[..=gt];
        let name: String = tag
            .trim_start_matches('<')
            .trim_start_matches('/')
            .chars()
            .take_while(|c| c.is_ascii_alphanumeric())
            .collect::<String>()
            .to_ascii_lowercase();
        let closing = tag.starts_with("</");
        match (name.as_str(), closing) {
            ("details", false) => out.push_str("<details>"),
            ("details", true) => out.push_str("</details>"),
            ("summary", false) => out.push_str("<summary>"),
            ("summary", true) => out.push_str("</summary>"),
            _ => {
                let _ = escape_html(&mut *out, tag);
            }
        }
        rest = &rest[gt + 1..];
    }
    let _ = escape_html(&mut *out, rest);
}

/// Renders Markdown to HTML that is safe to put in a page.
pub fn render_markdown(markdown: &str) -> String {
    let options = Options::ENABLE_TABLES
        | Options::ENABLE_STRIKETHROUGH
        | Options::ENABLE_TASKLISTS
        | Options::ENABLE_FOOTNOTES;
    let events = Parser::new_ext(markdown, options).map(|event| match event {
        Event::Html(h) | Event::InlineHtml(h) => {
            let mut safe = String::new();
            sanitize_raw_html(&h, &mut safe);
            Event::Html(CowStr::from(safe))
        }
        Event::Start(Tag::Image {
            link_type,
            dest_url,
            title,
            id,
        }) => {
            let url = rewrite_image_path(&dest_url);
            let url = if safe_url(&url) { url } else { String::new() };
            Event::Start(Tag::Image {
                link_type,
                dest_url: url.into(),
                title,
                id,
            })
        }
        Event::Start(Tag::Link {
            dest_url, title, ..
        }) => {
            if safe_url(&dest_url) {
                let mut a = String::from("<a href=\"");
                let _ = escape_href(&mut a, &dest_url);
                a.push('"');
                if !title.is_empty() {
                    a.push_str(" title=\"");
                    let _ = escape_html(&mut a, &title);
                    a.push('"');
                }
                if dest_url.starts_with("http") {
                    a.push_str(" target=\"_blank\" rel=\"noopener noreferrer\"");
                }
                a.push('>');
                Event::Html(a.into())
            } else {
                Event::Html("<a>".into())
            }
        }
        Event::End(TagEnd::Link) => Event::Html("</a>".into()),
        other => other,
    });
    let mut out = String::new();
    html::push_html(&mut out, events);
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rewrites_image_paths() {
        let html = render_markdown("![x](../../public/content/biology/a.svg)");
        assert!(html.contains("src=\"/content/biology/a.svg\""), "{html}");
    }

    #[test]
    fn dangerous_html_is_not_executed() {
        let html = render_markdown(
            "<script>alert(1)</script>\n\nText <img src=x onerror=alert(2)> [bad](javascript:alert(3)) ![i](javascript:alert(4))\n\n<details onclick=\"x()\"><summary>Key</summary>\n\nOpen\n</details>\n",
        );
        assert!(!html.contains("<script"), "{html}");
        assert!(!html.contains("<img src=x"), "{html}");
        assert!(!html.contains("javascript:"), "{html}");
        assert!(html.contains("<details><summary>Key</summary>"), "{html}");
        assert!(!html.contains("onclick"), "{html}");
        assert!(!html.contains("<details open"), "{html}");
    }

    #[test]
    fn external_links_open_in_a_new_tab() {
        let html = render_markdown("[v](https://example.com/a?b=1)");
        assert!(html.contains("target=\"_blank\""), "{html}");
        assert!(html.contains("noopener"), "{html}");
    }
}
