use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Flashcards;

impl Module for Flashcards {
    fn name(&self) -> &'static str {
        "flashcards"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/flashcards", index)
            .name("flashcards.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("flashcards/index.html", context! { title => "Flashcards" })
}
