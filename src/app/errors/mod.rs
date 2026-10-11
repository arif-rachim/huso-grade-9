use renox::prelude::*;

/// Placeholder: replaced by the real feature.
pub struct Errors;

impl Module for Errors {
    fn name(&self) -> &'static str {
        "errors"
    }

    fn routes(&self) -> Routes {
        Routes::new()
            .get("/errors", index)
            .name("errors.index")
            .require_auth()
    }
}

async fn index() -> View {
    view("errors/index.html", context! { title => "Error Log" })
}
