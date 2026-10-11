use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Today;

impl Module for Today {
    fn name(&self) -> &'static str {
        "today"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/today", index)
            .name("today.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("today/index.html", context! { title => "Today" })
}
