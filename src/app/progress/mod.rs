use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Progress;

impl Module for Progress {
    fn name(&self) -> &'static str {
        "progress"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/progress", index)
            .name("progress.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("progress/index.html", context! { title => "Progress" })
}
