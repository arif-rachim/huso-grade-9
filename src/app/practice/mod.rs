use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Practice;

impl Module for Practice {
    fn name(&self) -> &'static str {
        "practice"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/practice", index)
            .name("practice.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("practice/index.html", context! { title => "Practice" })
}
