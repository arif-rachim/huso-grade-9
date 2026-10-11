//! Image occlusion on the server.
//!
//! An `occlusion` card's `visual` is an SVG whose elements carry `data-label="..."`. One
//! review is made per label: the labelled element is hidden and the student says what it was.
//!
//! How an element is hidden: the element (and its children) is cut out of the SVG text, so the
//! answer is not even in the page source, and a grey rounded box with a "?" is drawn where it
//! was. The box comes from the element's bounding box, worked out from simple attributes:
//! `rect`, `circle`, `ellipse`, `line`, `polygon`, `polyline`, `text` (width estimated from the
//! font size) and `path` (the control points of `M L H V C S Q T Z` commands). A `translate(..)`
//! on the labelled element itself is applied; any other transform inside it, or a `path` with
//! arcs, means the box cannot be known. Then the element is still removed and a grey "?" badge
//! is drawn in the top-left corner of the picture instead, so nothing leaks either way.
//!
//! After the student reveals the answer the original picture is shown with a dashed outline in
//! the subject colour around the element (when its box is known).

use std::path::Path;

const GREY: &str = "#9ca3af";
const DARK_GREY: &str = "#6b7280";

#[derive(Debug, Clone)]
struct Tag {
    start: usize,
    end: usize,
    name: String,
    closing: bool,
    self_closing: bool,
    attrs: Vec<(String, String)>,
}

impl Tag {
    fn attr(&self, name: &str) -> Option<&str> {
        self.attrs
            .iter()
            .find(|(n, _)| n == name)
            .map(|(_, v)| v.as_str())
    }

    fn num(&self, name: &str) -> f64 {
        self.attr(name).and_then(parse_number).unwrap_or(0.0)
    }
}

fn parse_number(text: &str) -> Option<f64> {
    let t = text.trim().trim_end_matches("px");
    t.parse::<f64>().ok().filter(|n| n.is_finite())
}

/// Every start and end tag of the document, in order. Comments, `<!...>` and `<?...?>` are skipped.
fn scan(svg: &str) -> Vec<Tag> {
    let bytes = svg.as_bytes();
    let mut tags = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] != b'<' {
            i += 1;
            continue;
        }
        if svg[i..].starts_with("<!--") {
            i = svg[i..].find("-->").map_or(bytes.len(), |p| i + p + 3);
            continue;
        }
        if svg[i..].starts_with("<![CDATA[") {
            i = svg[i..].find("]]>").map_or(bytes.len(), |p| i + p + 3);
            continue;
        }
        // Find the closing '>' outside quotes.
        let mut j = i + 1;
        let mut quote: Option<u8> = None;
        while j < bytes.len() {
            match (quote, bytes[j]) {
                (Some(q), c) if c == q => quote = None,
                (None, b'"') | (None, b'\'') => quote = Some(bytes[j]),
                (None, b'>') => break,
                _ => {}
            }
            j += 1;
        }
        if j >= bytes.len() {
            break;
        }
        let inner = &svg[i + 1..j];
        if inner.starts_with('!') || inner.starts_with('?') {
            i = j + 1;
            continue;
        }
        let closing = inner.starts_with('/');
        let self_closing = inner.ends_with('/');
        let body = inner.trim_start_matches('/').trim_end_matches('/');
        let name_end = body
            .find(|c: char| c.is_whitespace())
            .unwrap_or(body.len());
        tags.push(Tag {
            start: i,
            end: j + 1,
            name: body[..name_end].to_owned(),
            closing,
            self_closing,
            attrs: parse_attrs(&body[name_end..]),
        });
        i = j + 1;
    }
    tags
}

fn parse_attrs(text: &str) -> Vec<(String, String)> {
    let mut out = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        while i < chars.len() && chars[i].is_whitespace() {
            i += 1;
        }
        let start = i;
        while i < chars.len() && !chars[i].is_whitespace() && chars[i] != '=' {
            i += 1;
        }
        let name: String = chars[start..i].iter().collect();
        while i < chars.len() && chars[i].is_whitespace() {
            i += 1;
        }
        if i < chars.len() && chars[i] == '=' {
            i += 1;
            while i < chars.len() && chars[i].is_whitespace() {
                i += 1;
            }
            let value: String = if i < chars.len() && (chars[i] == '"' || chars[i] == '\'') {
                let q = chars[i];
                i += 1;
                let s = i;
                while i < chars.len() && chars[i] != q {
                    i += 1;
                }
                let v = chars[s..i].iter().collect();
                i += 1;
                v
            } else {
                let s = i;
                while i < chars.len() && !chars[i].is_whitespace() {
                    i += 1;
                }
                chars[s..i].iter().collect()
            };
            if !name.is_empty() {
                out.push((name, value));
            }
        } else if !name.is_empty() {
            out.push((name, String::new()));
        }
    }
    out
}

/// The unique `data-label` values, in document order.
pub fn labels(svg: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();
    for tag in scan(svg).iter().filter(|t| !t.closing) {
        if let Some(label) = tag.attr("data-label") {
            let label = label.trim();
            if !label.is_empty() && !out.iter().any(|l| l == label) {
                out.push(label.to_owned());
            }
        }
    }
    out
}

/// The index range of the tags that make up the element at `idx`.
fn element(tags: &[Tag], idx: usize) -> (usize, usize) {
    if tags[idx].self_closing {
        return (idx, idx);
    }
    let name = &tags[idx].name;
    let mut depth = 0usize;
    for (j, t) in tags.iter().enumerate().skip(idx) {
        if &t.name != name {
            continue;
        }
        if t.closing {
            depth -= 1;
            if depth == 0 {
                return (idx, j);
            }
        } else if !t.self_closing {
            depth += 1;
        }
    }
    (idx, tags.len() - 1)
}

fn find_label(tags: &[Tag], label: &str) -> Option<usize> {
    tags.iter()
        .position(|t| !t.closing && t.attr("data-label").is_some_and(|l| l.trim() == label))
}

#[derive(Debug, Clone, Copy)]
struct BBox {
    x0: f64,
    y0: f64,
    x1: f64,
    y1: f64,
}

impl BBox {
    fn point(x: f64, y: f64) -> BBox {
        BBox {
            x0: x,
            y0: y,
            x1: x,
            y1: y,
        }
    }

    fn add(&mut self, x: f64, y: f64) {
        self.x0 = self.x0.min(x);
        self.y0 = self.y0.min(y);
        self.x1 = self.x1.max(x);
        self.y1 = self.y1.max(y);
    }

    fn union(self, other: BBox) -> BBox {
        BBox {
            x0: self.x0.min(other.x0),
            y0: self.y0.min(other.y0),
            x1: self.x1.max(other.x1),
            y1: self.y1.max(other.y1),
        }
    }

    fn grow(self, by: f64) -> BBox {
        BBox {
            x0: self.x0 - by,
            y0: self.y0 - by,
            x1: self.x1 + by,
            y1: self.y1 + by,
        }
    }
}

fn numbers(text: &str) -> Vec<f64> {
    text.split(|c: char| c == ',' || c.is_whitespace())
        .filter(|s| !s.is_empty())
        .filter_map(parse_number)
        .collect()
}

fn points_bbox(points: &str) -> Option<BBox> {
    let n = numbers(points);
    if n.len() < 2 {
        return None;
    }
    let mut b = BBox::point(n[0], n[1]);
    for pair in n.chunks_exact(2) {
        b.add(pair[0], pair[1]);
    }
    Some(b)
}

/// The box around a path's points; `None` for arcs and anything else it cannot follow.
fn path_bbox(d: &str) -> Option<BBox> {
    let mut chars = d.chars().peekable();
    let (mut cx, mut cy) = (0.0f64, 0.0f64);
    let (mut sx, mut sy) = (0.0f64, 0.0f64);
    let mut bbox: Option<BBox> = None;
    let push = |x: f64, y: f64, bbox: &mut Option<BBox>| match bbox {
        Some(b) => b.add(x, y),
        None => *bbox = Some(BBox::point(x, y)),
    };
    while let Some(&c) = chars.peek() {
        if c.is_whitespace() || c == ',' {
            chars.next();
            continue;
        }
        if !c.is_ascii_alphabetic() {
            return None;
        }
        chars.next();
        let mut args = String::new();
        while let Some(&n) = chars.peek() {
            if n.is_ascii_alphabetic() && n != 'e' && n != 'E' {
                break;
            }
            args.push(n);
            chars.next();
        }
        // Numbers can run together: "10-5" and "1.5.5" are two numbers each.
        let mut vals = Vec::new();
        let mut cur = String::new();
        for ch in args.chars() {
            let split = ch == ','
                || ch.is_whitespace()
                || (ch == '-' && !cur.is_empty() && !cur.ends_with(['e', 'E']))
                || (ch == '.' && cur.contains('.'));
            if split {
                if !cur.is_empty() {
                    vals.push(parse_number(&cur)?);
                    cur.clear();
                }
                if ch == '-' || ch == '.' {
                    cur.push(ch);
                }
            } else {
                cur.push(ch);
            }
        }
        if !cur.is_empty() {
            vals.push(parse_number(&cur)?);
        }
        let rel = c.is_ascii_lowercase();
        match c.to_ascii_uppercase() {
            'Z' => {
                cx = sx;
                cy = sy;
            }
            'H' => {
                for v in vals {
                    cx = if rel { cx + v } else { v };
                    push(cx, cy, &mut bbox);
                }
            }
            'V' => {
                for v in vals {
                    cy = if rel { cy + v } else { v };
                    push(cx, cy, &mut bbox);
                }
            }
            'M' | 'L' | 'T' | 'S' | 'Q' | 'C' => {
                let group = match c.to_ascii_uppercase() {
                    'M' | 'L' | 'T' => 2,
                    'S' | 'Q' => 4,
                    _ => 6,
                };
                if vals.is_empty() || vals.len() % group != 0 {
                    return None;
                }
                for chunk in vals.chunks(group) {
                    let (bx, by) = (cx, cy);
                    for pair in chunk.chunks(2) {
                        let (x, y) = if rel {
                            (bx + pair[0], by + pair[1])
                        } else {
                            (pair[0], pair[1])
                        };
                        push(x, y, &mut bbox);
                    }
                    let n = chunk.len();
                    cx = if rel { bx + chunk[n - 2] } else { chunk[n - 2] };
                    cy = if rel { by + chunk[n - 1] } else { chunk[n - 1] };
                    if c.to_ascii_uppercase() == 'M' {
                        sx = cx;
                        sy = cy;
                    }
                }
            }
            _ => return None, // arcs (A) and unknown commands
        }
    }
    bbox
}

fn text_of(svg: &str, tags: &[Tag], k: usize) -> String {
    let (_, last) = element(tags, k);
    let from = tags[k].end;
    let to = tags[last].start.max(from);
    let mut out = String::new();
    let mut in_tag = false;
    for ch in svg[from..to].chars() {
        match ch {
            '<' => in_tag = true,
            '>' => in_tag = false,
            c if !in_tag => out.push(c),
            _ => {}
        }
    }
    out.trim().to_owned()
}

fn tag_bbox(svg: &str, tags: &[Tag], k: usize) -> Option<BBox> {
    let t = &tags[k];
    let stroke = t.attr("stroke-width").and_then(parse_number).unwrap_or(1.0);
    let b = match t.name.as_str() {
        "rect" | "image" | "foreignObject" => {
            let (x, y) = (t.num("x"), t.num("y"));
            BBox {
                x0: x,
                y0: y,
                x1: x + t.num("width"),
                y1: y + t.num("height"),
            }
        }
        "circle" => {
            let r = t.num("r");
            BBox {
                x0: t.num("cx") - r,
                y0: t.num("cy") - r,
                x1: t.num("cx") + r,
                y1: t.num("cy") + r,
            }
        }
        "ellipse" => BBox {
            x0: t.num("cx") - t.num("rx"),
            y0: t.num("cy") - t.num("ry"),
            x1: t.num("cx") + t.num("rx"),
            y1: t.num("cy") + t.num("ry"),
        },
        "line" => {
            let mut b = BBox::point(t.num("x1"), t.num("y1"));
            b.add(t.num("x2"), t.num("y2"));
            b
        }
        "polygon" | "polyline" => points_bbox(t.attr("points")?)?,
        "path" => path_bbox(t.attr("d")?)?,
        "text" => {
            let size = t.attr("font-size").and_then(parse_number).unwrap_or(14.0);
            let chars = text_of(svg, tags, k).chars().count().max(1) as f64;
            let width = chars * size * 0.6;
            let x = t.num("x");
            let left = match t.attr("text-anchor") {
                Some("middle") => x - width / 2.0,
                Some("end") => x - width,
                _ => x,
            };
            let y = t.num("y");
            BBox {
                x0: left,
                y0: y - size * 0.95,
                x1: left + width,
                y1: y + size * 0.3,
            }
        }
        // Containers and tspans add nothing of their own.
        "g" | "tspan" | "title" | "desc" | "defs" => return Some(BBox::point(f64::NAN, f64::NAN)),
        _ => return None,
    };
    Some(b.grow(stroke / 2.0))
}

/// `translate(x[, y])` as an offset; `Err` for any other transform.
fn translation(transform: Option<&str>) -> Result<(f64, f64), ()> {
    let Some(t) = transform else {
        return Ok((0.0, 0.0));
    };
    let t = t.trim();
    let inner = t
        .strip_prefix("translate(")
        .and_then(|r| r.strip_suffix(')'))
        .ok_or(())?;
    let n = numbers(inner);
    match n.as_slice() {
        [x] => Ok((*x, 0.0)),
        [x, y] => Ok((*x, *y)),
        _ => Err(()),
    }
}

/// The box around the labelled element, in the coordinates of its parent.
fn element_bbox(svg: &str, tags: &[Tag], idx: usize) -> Option<BBox> {
    let (first, last) = element(tags, idx);
    let (dx, dy) = translation(tags[first].attr("transform")).ok()?;
    let mut acc: Option<BBox> = None;
    for k in first..=last {
        let t = &tags[k];
        if t.closing {
            continue;
        }
        if k != first && t.attr("transform").is_some() {
            return None;
        }
        let b = tag_bbox(svg, tags, k);
        // `g` returns a NaN marker: skipped. A shape we cannot measure fails the whole box.
        let b = match b {
            Some(b) if b.x0.is_nan() => continue,
            Some(b) => b,
            None => return None,
        };
        acc = Some(acc.map_or(b, |a| a.union(b)));
    }
    let b = acc?;
    Some(BBox {
        x0: b.x0 + dx,
        y0: b.y0 + dy,
        x1: b.x1 + dx,
        y1: b.y1 + dy,
    })
}

fn fmt(n: f64) -> String {
    let s = format!("{n:.1}");
    s.trim_end_matches(".0").to_owned()
}

fn cover(b: BBox) -> String {
    let b = b.grow(3.0);
    let (w, h) = (b.x1 - b.x0, b.y1 - b.y0);
    let size = (h * 0.7).clamp(10.0, 22.0);
    format!(
        "<g class=\"fc-occluded\"><rect x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\" rx=\"4\" fill=\"{GREY}\" stroke=\"{DARK_GREY}\" stroke-width=\"1.5\"/><text x=\"{}\" y=\"{}\" text-anchor=\"middle\" font-family=\"sans-serif\" font-size=\"{}\" font-weight=\"bold\" fill=\"#ffffff\">?</text></g>",
        fmt(b.x0),
        fmt(b.y0),
        fmt(w),
        fmt(h),
        fmt(b.x0 + w / 2.0),
        fmt(b.y0 + h / 2.0 + size * 0.35),
        fmt(size),
    )
}

/// A grey "?" badge in the top-left corner, used when the element's box is unknown.
fn corner_badge(tags: &[Tag]) -> String {
    let root = tags.iter().find(|t| !t.closing && t.name == "svg");
    let (mut x, mut y) = (0.0, 0.0);
    if let Some(vb) = root.and_then(|r| r.attr("viewBox")) {
        let n = numbers(vb);
        if n.len() == 4 {
            x = n[0];
            y = n[1];
        }
    }
    cover(BBox {
        x0: x + 6.0,
        y0: y + 6.0,
        x1: x + 46.0,
        y1: y + 30.0,
    })
}

/// The picture with the element labelled `label` hidden behind a grey box.
pub fn hide_label(svg: &str, label: &str) -> String {
    let tags = scan(svg);
    let Some(idx) = find_label(&tags, label) else {
        return svg.to_owned();
    };
    let (first, last) = element(&tags, idx);
    let (from, to) = (tags[first].start, tags[last].end);
    match element_bbox(svg, &tags, idx) {
        Some(b) => format!("{}{}{}", &svg[..from], cover(b), &svg[to..]),
        None => {
            let badge = corner_badge(&tags);
            let without = format!("{}{}", &svg[..from], &svg[to..]);
            // Last, so it is drawn on top of the background.
            match without.rfind("</svg>") {
                Some(at) => format!("{}{}{}", &without[..at], badge, &without[at..]),
                None => without,
            }
        }
    }
}

/// The whole picture with a dashed outline around the element labelled `label`.
pub fn mark_label(svg: &str, label: &str, color: &str) -> String {
    let tags = scan(svg);
    let Some(idx) = find_label(&tags, label) else {
        return svg.to_owned();
    };
    let Some(b) = element_bbox(svg, &tags, idx) else {
        return svg.to_owned();
    };
    let (_, last) = element(&tags, idx);
    let b = b.grow(3.0);
    let outline = format!(
        "<rect class=\"fc-marked\" x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\" rx=\"4\" fill=\"none\" stroke=\"{}\" stroke-width=\"2.5\" stroke-dasharray=\"6 3\"/>",
        fmt(b.x0),
        fmt(b.y0),
        fmt(b.x1 - b.x0),
        fmt(b.y1 - b.y0),
        color
    );
    let at = tags[last].end;
    format!("{}{}{}", &svg[..at], outline, &svg[at..])
}

/// Reads `visual` (a path under `public/`, such as `content/biology/cell.svg`) when it is a
/// plain, safe SVG file that can be put in the page. `None` means: show it with `<img>`.
pub fn read(public_dir: &Path, visual: &str) -> Option<String> {
    let rel = Path::new(visual);
    if !visual.ends_with(".svg")
        || rel.is_absolute()
        || rel
            .components()
            .any(|c| !matches!(c, std::path::Component::Normal(_)))
    {
        return None;
    }
    let text = std::fs::read_to_string(public_dir.join(rel)).ok()?;
    let lower = text.to_ascii_lowercase();
    if lower.contains("<script") || lower.contains("javascript:") || lower.contains(" onload=") {
        return None;
    }
    // Start at the <svg> element: drop an XML prolog and doctype.
    let start = text.find("<svg")?;
    Some(text[start..].to_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    const CELL: &str = r##"<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 100">
  <rect x="0" y="0" width="200" height="100" fill="#fff"/>
  <circle data-label="Nucleus" cx="100" cy="50" r="20" fill="#16a34a"/>
  <g data-label="Membrane">
    <rect x="10" y="10" width="30" height="20" stroke-width="2"/>
    <text x="25" y="60" font-size="10" text-anchor="middle">membrane</text>
  </g>
  <text data-label="Cytoplasm" x="150" y="80" font-size="12">Cytoplasm</text>
  <line data-label="Wall" x1="5" y1="90" x2="195" y2="90"/>
  <path data-label="Curve" d="M 10 10 L 20 30 C 30 40, 40 50, 50 60"/>
  <path data-label="Arc" d="M 10 10 A 5 5 0 0 1 20 20"/>
  <g data-label="Rotated"><rect x="1" y="1" width="5" height="5" transform="rotate(45)"/></g>
  <g data-label="Moved" transform="translate(100, 20)"><rect x="0" y="0" width="10" height="10"/></g>
</svg>"##;

    #[test]
    fn finds_labels_in_order_once_each() {
        let svg = r#"<svg><g data-label="B"/><g data-label="A"><circle data-label="A"/></g><g data-label=" "/></svg>"#;
        assert_eq!(labels(svg), ["B", "A"]);
        assert_eq!(labels("<svg><rect/></svg>"), Vec::<String>::new());
        assert_eq!(
            labels(CELL),
            [
                "Nucleus",
                "Membrane",
                "Cytoplasm",
                "Wall",
                "Curve",
                "Arc",
                "Rotated",
                "Moved"
            ]
        );
    }

    #[test]
    fn a_circle_is_replaced_by_a_grey_box_with_a_question_mark() {
        let out = hide_label(CELL, "Nucleus");
        assert!(!out.contains("Nucleus"), "the answer must not stay in the page");
        assert!(!out.contains("<circle"));
        assert!(out.contains("fc-occluded"));
        assert!(out.contains(">?</text>"));
        // r=20 around (100, 50), plus 0.5 stroke, plus 3 padding.
        assert!(out.contains("x=\"76.5\" y=\"26.5\" width=\"47\" height=\"47\""), "{out}");
        // Other labels stay.
        assert!(out.contains("Cytoplasm"));
    }

    #[test]
    fn a_group_uses_the_box_around_all_of_its_children() {
        let out = hide_label(CELL, "Membrane");
        assert!(!out.contains("membrane</text>"));
        assert!(out.contains("fc-occluded"));
        assert!(!out.contains("corner"));
        // The rect spans 9..41 (stroke 2); the text is 8 chars * 6 = 48 wide, centred on 25: 1..49.
        assert!(out.contains("x=\"-2.5\""), "{out}");
    }

    #[test]
    fn text_and_lines_and_paths_have_boxes() {
        for label in ["Cytoplasm", "Wall", "Curve"] {
            let out = hide_label(CELL, label);
            assert!(out.contains("fc-occluded"), "{label}");
            assert!(!out.contains(&format!("data-label=\"{label}\"")), "{label}");
        }
    }

    #[test]
    fn a_translate_on_the_element_moves_the_box() {
        let out = hide_label(CELL, "Moved");
        // The rect is 0..10, moved to 100..110 / 20..30, plus stroke and padding.
        assert!(out.contains("x=\"96.5\" y=\"16.5\""), "{out}");
    }

    #[test]
    fn unknown_boxes_fall_back_to_a_corner_badge_and_still_remove_the_element() {
        for label in ["Arc", "Rotated"] {
            let out = hide_label(CELL, label);
            assert!(!out.contains(&format!("data-label=\"{label}\"")), "{label}");
            assert!(out.contains("fc-occluded"), "{label}");
            assert!(out.contains("x=\"3\" y=\"3\""), "{label}: {out}");
        }
    }

    #[test]
    fn an_unknown_label_changes_nothing() {
        assert_eq!(hide_label(CELL, "Nope"), CELL);
        assert_eq!(mark_label(CELL, "Nope", "#16a34a"), CELL);
    }

    #[test]
    fn marking_keeps_the_picture_and_adds_a_dashed_outline() {
        let out = mark_label(CELL, "Nucleus", "#16a34a");
        assert!(out.contains("<circle data-label=\"Nucleus\""));
        assert!(out.contains("fc-marked"));
        assert!(out.contains("stroke=\"#16a34a\""));
        // No box known: unchanged.
        assert_eq!(mark_label(CELL, "Arc", "#16a34a"), CELL);
    }

    #[test]
    fn path_boxes_follow_absolute_and_relative_commands() {
        let b = path_bbox("M10 10 H 50 V 30 z").unwrap();
        assert_eq!((b.x0, b.y0, b.x1, b.y1), (10.0, 10.0, 50.0, 30.0));
        let b = path_bbox("m10 10 l5-5 h10").unwrap();
        assert_eq!((b.x0, b.y0, b.x1, b.y1), (10.0, 5.0, 25.0, 10.0));
        assert!(path_bbox("M0 0 A5 5 0 0 1 9 9").is_none());
        assert!(path_bbox("").is_none());
    }

    #[test]
    fn comments_and_quoted_angle_brackets_do_not_confuse_the_scanner() {
        let svg = r#"<svg><!-- <g data-label="Ghost"> --><text data-label="A>B" x="1" y="1">a</text></svg>"#;
        assert_eq!(labels(svg), ["A>B"]);
    }

    #[test]
    fn read_only_serves_plain_svg_files_under_public() {
        let dir = std::env::temp_dir().join(format!("huso-svg-{}", std::process::id()));
        std::fs::create_dir_all(dir.join("content")).unwrap();
        std::fs::write(dir.join("content/ok.svg"), "<?xml version=\"1.0\"?>\n<svg><g/></svg>").unwrap();
        std::fs::write(dir.join("content/bad.svg"), "<svg><script>x</script></svg>").unwrap();
        assert_eq!(read(&dir, "content/ok.svg").as_deref(), Some("<svg><g/></svg>"));
        assert_eq!(read(&dir, "content/bad.svg"), None);
        assert_eq!(read(&dir, "../etc/passwd.svg"), None);
        assert_eq!(read(&dir, "/etc/passwd.svg"), None);
        assert_eq!(read(&dir, "content/missing.svg"), None);
        assert_eq!(read(&dir, "content/ok.png"), None);
        std::fs::remove_dir_all(&dir).ok();
    }
}
