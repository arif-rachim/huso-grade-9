use renox::prelude::*;
use serde::Deserialize;

pub struct Home;

impl Module for Home {
    fn name(&self) -> &'static str {
        "home"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/", index)
            .name("home")
            .get("/log-in-first", login_required)
            .name("login.required")
    }
}

/// Everyone starts at today's plan: guests may look around and study, and only log in
/// when they want to answer questions or save something.
async fn index() -> Redirect {
    Redirect::to("/today")
}

#[derive(Deserialize)]
struct Needed {
    next: Option<String>,
    why: Option<String>,
}

/// The message shown on the login page for a login-gated control (`why` is a fixed key).
fn reason(why: Option<&str>) -> &'static str {
    match why {
        Some("tick") => "Log in to tick off tasks and save your progress.",
        Some("review") => "Log in to review flashcards and save your progress.",
        Some("save") => "Log in to save your work.",
        _ => "Log in to answer questions and save your progress.",
    }
}

/// A site-local path only (no scheme, no `//host`, no backslash).
fn local_path(path: &str) -> bool {
    path.starts_with('/') && !path.starts_with("//") && !path.contains('\\')
}

/// Where login-gated buttons and links for guests point: it remembers the page to come back
/// to (`next`), explains why a login is needed, and goes to the login page.
async fn login_required(
    user: Option<AuthUser>,
    session: Session,
    Query(q): Query<Needed>,
) -> Result<Redirect> {
    let next = q.next.filter(|n| local_path(n));
    if user.is_some() {
        return Ok(Redirect::to(next.as_deref().unwrap_or("/today")));
    }
    if let Some(next) = next {
        // The same key `Redirect::intended` reads after a successful login.
        session.put("_intended", next)?;
    }
    session.flash("status", reason(q.why.as_deref()))?;
    Ok(Redirect::to("/login"))
}
