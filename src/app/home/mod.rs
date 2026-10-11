use renox::prelude::*;

pub struct Home;

impl Module for Home {
    fn name(&self) -> &'static str {
        "home"
    }

    fn routes(&self) -> Routes {
        Routes::new().get("/", index).name("home")
    }
}

/// Guests go to the login page, everyone else to today's plan.
async fn index(user: Option<AuthUser>) -> Redirect {
    match user {
        Some(_) => Redirect::to("/today"),
        None => Redirect::to("/login"),
    }
}
